# Load Profit Ranker — Formula Spec (v1)

**Status:** Formula drafted (rev 2: trip context, 70-hr cycle, target, pickup warning). Benchmarks checked against sources on Oct 4, 2026. Dad's real numbers still pending (see §8).

---

## 0. Instructions for Claude Code (plan mode)

- This file is the **source of truth for the calculation engine**. Plan v1 only (§2–§5). Everything in §7 marked *Deferred* or *Removed* is out of scope. Do not implement it.
- The engine must be a **pure module**: numbers in, results out. No UI, no network calls, no routing API inside it. Miles arrive as plain numbers from a separate routing layer.
- Put every constant and default in **one config object**. Every default must be overridable from the truck settings.
- Use the worked example in §6 as **unit-test fixtures**. Results must match within ±$0.01 (or ±0.0001 for day counts).
- Keep full precision through the math. Round only for display.
- Produce a plan for review before writing any code.

---

## 1. What the formula answers

> "Of these 2–3 loads, which one puts the most money in Dad's pocket **per day of truck time**?"

- **Primary ranking metric:** profit per day
- **Secondary metric (tie-breaker):** profit per total mile, deadhead included
- **Shown for comparison:** board rate per loaded mile, the number load boards advertise. Showing it next to true profit per mile is the point of the app.

---

## 2. Formula at a glance

```
totalMiles     = deadheadMiles + loadedMiles
driveHours     = totalMiles / avgSpeedMph
dutyHours      = driveHours + dockWaitHours + bufferHours
restartNeeded  = dutyHours > cycleHoursRemaining
hosDays        = max(driveHours / maxDriveHours, dutyHours / maxDutyHours)
                 + (restartHours / 24 if restartNeeded else 0)
                 (ceil(hosDays) only if daysRoundingMode = "whole", applied after the restart is added)
scheduleDays   = deliveryDate − availableDate   (calendar days; 0 if no delivery date)
daysUsed       = max(hosDays, scheduleDays)

grossRevenue   = postedRate × payoutPercent / 100
fuelCost       = totalMiles / mpg × dieselPrice
perMileCost    = totalMiles × (maintenanceCpm + tiresCpm + otherCpm)
variableCost   = fuelCost + perMileCost + tolls
fixedCost      = monthlyFixedCosts / workingDaysPerMonth × daysUsed

netProfit      = grossRevenue − variableCost − fixedCost
profitPerDay   = netProfit / daysUsed        ← RANKING METRIC
profitPerMile  = netProfit / totalMiles
boardRate      = postedRate / loadedMiles    (display only)
meetsTarget    = profitPerDay >= targetProfitPerDay   (null if no target set)
```

---

## 3. Inputs

### 3a. Trip context (entered once per comparison, top of the compare screen)

These change every time Dad compares loads, so they aren't truck settings.

| Field | Unit | Required | Default |
|---|---|---|---|
| `currentLocation` | city/address | yes | last location used |
| `availableDate` | date | yes | today. **Passed in by the caller. The engine never reads the clock** |
| `cycleHoursRemaining` | hours | no | 70 (fresh off a restart). Copied from the ELD "cycle remaining" screen |

### 3b. Per load (Dad enters, max 3 loads in v1)

| Field | Unit | How it's obtained | Required | Default |
|---|---|---|---|---|
| `pickupLocation` | city/address | typed | yes | — |
| `dropoffLocation` | city/address | typed | yes | — |
| `loadedMiles` | miles | typed in R1; filled by the routing layer (pickup → drop-off) in R1.5, always overridable | yes | — |
| `deadheadMiles` | miles | typed in R1; filled by the routing layer (current location → pickup) in R1.5, always overridable | yes | — |
| `postedRate` | $ | typed | yes | — |
| `pickupDate` | date | typed | no | — (validation only in v1) |
| `deliveryDate` | date | typed | no | — (drives `scheduleDays`) |
| `dockWaitHours` | hours | typed | no | 2 *(estimate)* |
| `tolls` | $ | typed | no | 0 |

### 3c. Truck settings (set once, editable)

| Field | Unit | Default | Source / status |
|---|---|---|---|
| `mpg` | mi/gal | 6.5 | **Estimate.** Not verified. Replace with Dad's real number |
| `fuelRegion` | EIA PADD region | PADD 1C (Lower Atlantic, incl. VA) | Where Dad mostly fuels (§8 Q5) |
| `dieselPrice` | $/gal | auto | **Automatic:** latest weekly EIA on-highway diesel price for `fuelRegion`. A manual override (pump or fuel-card price) wins when set. Fallback if no EIA data yet: 6.38 (EIA US average, week of Sep 28, 2026) |
| `maintenanceCpm` | $/mile | 0.215 | ATRI 2026 Operational Costs (2025 data) |
| `tiresCpm` | $/mile | 0.050 | ATRI 2026 Operational Costs (2025 data) |
| `otherCpm` | $/mile | 0 | Dad's extra per-mile costs, if any |
| `monthlyFixedCosts` | $/month | **none** | Dad, required: truck payment + insurance + permits + other fixed bills. No silent default, because profit/day is meaningless without it. Prompt for it. |
| `payoutPercent` | % | 100 | 100 = own authority. Lower if leased onto a carrier (§8 Q1) |
| `daysRoundingMode` | enum | `"fractional"` | `"fractional"` or `"whole"` (§7 explains why) |
| `targetProfitPerDay` | $/day | none (optional) | Dad's minimum. When set, each load shows whether it meets it. Makes single-load checks useful |

### 3d. Engine constants (config, not on the main form)

| Constant | Value | Source / status |
|---|---|---|
| `avgSpeedMph` | 50 | Planning estimate that includes stops. Not a regulation |
| `maxDriveHours` | 11 | FMCSA hours-of-service rules (49 CFR Part 395) |
| `maxDutyHours` | 14 | FMCSA hours-of-service rules (49 CFR Part 395) |
| `maxCycleHours` | 70 | FMCSA 70-hour/8-day limit (60/7 for carriers that don't run every day, §8 Q10) |
| `restartHours` | 34 | FMCSA 34-hour restart |
| `bufferHours` | 2 | **Estimate:** pre-trip inspection, fueling, actual load/unload time beyond the dock wait |
| `workingDaysPerMonth` | 30 | **Placeholder.** Should be the number of days Dad actually works per month (§8 Q6) |

---

## 4. Calculation steps (in order)

1. **Miles:** `totalMiles = deadheadMiles + loadedMiles`
2. **HOS time:**
   - `driveHours = totalMiles / avgSpeedMph`
   - `dutyHours = driveHours + dockWaitHours + bufferHours`
   - `hosDays = max(driveHours / 11, dutyHours / 14)`
   - **Cycle check:** if `dutyHours > cycleHoursRemaining`, set `restartNeeded = true` and add `restartHours / 24` (1.4167) to `hosDays`
   - If `daysRoundingMode == "whole"`: `hosDays = ceil(hosDays)` (after the restart is added)
3. **Schedule time:** `scheduleDays = deliveryDate − availableDate` in whole calendar days. Use 0 if there's no delivery date.
4. **Days used:** `daysUsed = max(hosDays, scheduleDays)`. Record which one won (`"hos"` or `"schedule"`) so the UI can say "tied up waiting for the delivery appointment."
5. **Revenue:** `grossRevenue = postedRate × payoutPercent / 100`
6. **Variable costs:**
   - `fuelCost = totalMiles / mpg × dieselPrice`
   - `perMileCost = totalMiles × (maintenanceCpm + tiresCpm + otherCpm)`
   - `variableCost = fuelCost + perMileCost + tolls`
7. **Fixed costs:** `fixedCost = (monthlyFixedCosts / workingDaysPerMonth) × daysUsed`
8. **Net:** `netProfit = grossRevenue − variableCost − fixedCost`
9. **Target:** `meetsTarget = profitPerDay >= targetProfitPerDay`, or null if no target is set.
10. **Outputs per load:** `netProfit`, `profitPerDay`, `profitPerMile`, `boardRate`, `daysUsed`, `daysBoundBy`, `restartNeeded`, `meetsTarget`, warnings (§5), plus the full cost breakdown (fuel, per-mile, tolls, fixed)
11. **Rank:** sort by `profitPerDay` descending, using `profitPerMile` as the tie-breaker. Flag any load with `netProfit < 0` as **"Loses money."** Mark the winner.
12. **Why it won:** for the winner and the runner-up, divide each line (revenue, fuel, per-mile, tolls, fixed) by that load's `daysUsed`. Show the 2 lines where the winner's per-day advantage is largest. Per-day, not raw dollars, so the explanation agrees with the ranking.

---

## 5. Validation & edge cases

| Case | Behavior |
|---|---|
| `loadedMiles <= 0` | Error: routing failed or same pickup/drop-off |
| `deadheadMiles < 0` | Error |
| `mpg <= 0` or `dieselPrice <= 0` | Error in settings |
| `monthlyFixedCosts` missing | Block results and prompt Dad to enter it |
| `deliveryDate < availableDate` | Error |
| `pickupDate > deliveryDate` | Error |
| `payoutPercent` outside 1–100 | Error |
| `cycleHoursRemaining` outside 0–`maxCycleHours` | Error |
| `targetProfitPerDay < 0` | Error |
| `pickupDate < availableDate`, or `deadheadMiles / avgSpeedMph > maxDriveHours × (pickupDate − availableDate + 1)` | **Warning** "May not make this pickup in time." Still computed and ranked (brokers often move pickups) |
| `restartNeeded` | **Warning** "Needs a 34-hr restart." Still ranked |
| Negative `netProfit` | Valid result. Show it as a loss and rank it normally |
| Fewer than 2 loads | Still compute; show the breakdown with no ranking |

`daysUsed` is always > 0 because `loadedMiles > 0`, so there's no divide-by-zero.

---

## 6. Worked example (use as unit-test fixtures)

**Settings:** mpg 6.5 · diesel $6.38 · maintenance $0.215/mi · tires $0.050/mi · other $0 · monthly fixed **$5,000 (placeholder, not Dad's number)** · payout 100% · working days 30 · speed 50 · buffer 2 h · rounding `fractional`

**Loads** (miles are illustrative, not real routing):

| | Rate | Deadhead | Loaded | Dock wait | Tolls | scheduleDays |
|---|---|---|---|---|---|---|
| A | $2,400 | 15 | 650 | 2 h | $0 | 1 |
| B | $3,000 | 200 | 1,000 | 2 h | $35 | 2 |
| C | $1,900 | 40 | 500 | 1 h | $0 | 3 |

**Expected results (fractional):**

| | A | B | C |
|---|---|---|---|
| totalMiles | 665 | 1,200 | 540 |
| driveHours | 13.3 | 24.0 | 10.8 |
| dutyHours | 17.3 | 28.0 | 13.8 |
| hosDays | 1.2357 | 2.1818 | 0.9857 |
| **daysUsed** | **1.2357** (hos) | **2.1818** (hos) | **3.0000** (schedule) |
| grossRevenue | 2,400.00 | 3,000.00 | 1,900.00 |
| fuelCost | 652.72 | 1,177.85 | 530.03 |
| perMileCost | 176.225 | 318.00 | 143.10 |
| tolls | 0.00 | 35.00 | 0.00 |
| fixedCost | 205.95 | 363.64 | 500.00 |
| **netProfit** | **1,365.10** | **1,105.52** | **726.87** |
| **profitPerDay** | **1,104.70** | **506.70** | **242.29** |
| profitPerMile | 2.0528 | 0.9213 | 1.3461 |
| boardRate (per loaded mile) | 3.6923 | 3.0000 | 3.8000 |
| **Rank** | **1** | **2** | **3** |

**What the example proves:**
- **B** has the biggest check but loses to A. The 200 deadhead miles and the extra day eat the extra $600.
- **C** has the *highest* board rate per loaded mile ($3.80) but ranks *last*. Its delivery appointment ties the truck up for 3 days even though it's under a day of driving.

**Rounding-mode test** (same inputs, `daysRoundingMode = "whole"`):

| | A | B | C |
|---|---|---|---|
| daysUsed | 2 | 3 | 3 |
| netProfit | 1,237.72 | 969.15 | 726.87 |
| profitPerDay | 618.86 | 323.05 | 242.29 |

The ranking is the same here, but the gaps change a lot. That's why rounding mode is a setting to decide with Dad.

**Cycle-limit test** (same inputs, `cycleHoursRemaining = 20`):

| | A | B | C |
|---|---|---|---|
| dutyHours | 17.3 | 28.0 | 13.8 |
| restartNeeded | no | **yes** | no |
| hosDays | 1.2357 | **3.5985** | 0.9857 |
| daysUsed (fractional) | 1.2357 | **3.5985** | 3.0000 |
| fixedCost | 205.95 | **599.75** | 500.00 |
| netProfit | 1,365.10 | **869.41** | 726.87 |
| profitPerDay | 1,104.70 | **241.60** | 242.29 |
| profitPerMile | 2.0528 | 0.7245 | 1.3461 |
| **Rank** | **1** | **3** | **2** |

Same inputs in `"whole"` mode: daysUsed 2 / 4 / 3 · netProfit 1,237.72 / 802.49 / 726.87 · profitPerDay 618.86 / 200.62 / 242.29 (rank A, C, B).

**What it proves:** running low on cycle hours **flips B below C**. The 34-hour restart makes B the slowest load.

**Target test** (worked-example inputs, fractional, `targetProfitPerDay = 600`): A meets the target (1,104.70); B (506.70) and C (242.29) don't. With no target set, `meetsTarget` is null for all three.

---

## 7. Changes from the Gemini draft, and why

| Gemini item | Decision | Reason |
|---|---|---|
| Diesel $6.38 (EIA, Sept 2026) | **Kept** | Verified: EIA week of Sep 28, 2026. Very volatile (record $6.53 the week before), so it must be updated weekly |
| Maintenance $0.220/mi | **Corrected → $0.215** | ATRI 2026 report gives $0.215 |
| Tires $0.050/mi | **Kept** | Verified, ATRI 2026 |
| Tolls $0.043/mi (ATRI average) | **Removed** | Dad enters real tolls per load. Using both double-counts |
| Deadhead default 16.7% of loaded miles | **Removed** | The app computes actual deadhead from current location to pickup. A fleet average only makes sense for annual budgeting |
| Round days UP to whole days | **Changed → fractional by default, whole as a setting** | Rounding creates cliffs. A load needing 11.1 driving hours counts as 2 full days, the same as one needing 22, which can flip rankings over a few miles. The right choice depends on how Dad actually works (§8 Q7) |
| Pickup/delivery dates (ignored by Gemini) | **Added `scheduleDays`** | A load with a far-out delivery appointment ties up the truck even if driving is short (see Load C) |
| `driverWagePerMile` deducted as an expense | **Removed** | For an owner-operator, Dad's take-home *is* the profit. Subtracting an invented wage double-counts him. Because it's per mile, it also biases rankings against longer loads |
| `taxReservePercent` | **Removed from ranking** | A flat percentage scales every load equally, so it can never change the ranking. Applied to a loss, it creates a fake tax credit. Taxes are annual, not per load |
| Broker grade A–D (0/2/5/10% deductions) | **Deferred** | The percentages have no source, and it adds a field to every entry, which slows Dad down. Later alternative: a single "risky broker" checkbox, or the credit/days-to-pay score his load board already shows |
| Terrain penalty (−1/−2 MPG) | **Deferred** | Unsourced, and terrain varies along a single route. Separate loaded vs. empty MPG from Dad's fuel records would be more useful later |
| Worst-case +6 h delay / "High Risk" flag | **Deferred to v1.1** | Cheap to add, but the 6 h is arbitrary. Set it from Dad's experience of real delays |
| Round-trip proxy using outbound market rate "pulled via load board API" | **Removed from v1** | Contradicts the project's key constraint: no load board data. Later alternative: Dad tags the drop-off market as strong / average / weak himself |

### 7b. Known simplifications (check against Dad's real loads)

- The 10-hour off-duty reset and the 30-minute break aren't modeled separately. They're folded into `avgSpeedMph` and the 11/14-hour day units.
- At most one 34-hour restart per load. Loads long enough to need two aren't handled.
- `cycleHoursRemaining` is treated as a single number. Hours rolling off the 8-day window during the trip are ignored, which is conservative.
- `hosDays` mixes "duty-day" units (11 h / 14 h) with restart time in calendar days (34 h / 24). It's an approximation, applied the same way to every load.
- Dates are whole calendar days; no appointment times.
- ATRI per-mile costs are fleet-wide averages, not Dad's numbers.

---

## 8. Open questions for Dad (answer before trusting results)

1. **Setup:** own authority, leased onto a carrier, or company driver? This sets `payoutPercent`. If leased, how is the fuel surcharge paid? If he's a company driver paid per mile, this app doesn't fit and the idea needs rethinking.
2. **MPG:** what does he really get, loaded vs. empty?
3. **Monthly fixed costs:** truck payment, insurance, permits/plates, ELD, phone, parking, anything else. What's the total?
4. **Maintenance and tires:** roughly what he spends per year, divided by miles per year. ATRI averages are fleet-wide, and small fleets run higher.
5. **Fuel:** does he get a fuel card discount? That changes his effective `dieselPrice`. Which region does he mostly fuel in? That sets `fuelRegion`.
6. **Working days:** how many days a month is he actually working? This sets `workingDaysPerMonth`.
7. **Rounding:** when he finishes a load at midday, does he usually get rolling again that day, or is the day effectively done? This decides `daysRoundingMode`.
8. **Typical dock wait** at the shippers and receivers he deals with.
9. **His current rule:** how does he decide yes/no today? Run 3 of his real past loads through §2 on paper. He should agree with each verdict, or you should understand why not. (This is the M0 test.)
10. **HOS cycle:** is he on 70/8 or 60/7? Does he use the 34-hour restart, or let hours roll off?
11. **Minimum:** what's the lowest profit per day he'd accept? That sets `targetProfitPerDay`.

---

## 9. Sources (checked Oct 4, 2026)

- ATRI, *An Analysis of the Operational Costs of Trucking: 2026 Update* — https://truckingresearch.org/2026/07/analysis-of-the-operational-costs-of-trucking-2026-update/
- ATRI press release, Jul 15, 2026 — https://truckingresearch.org/2026/07/new-atri-report-details-accelerating-costs-and-low-profitability-despite-cuts/
- Repair & maintenance $0.215/mi, tires $0.05/mi (ATRI 2026, reported by The Trucker) — https://www.thetrucker.com/trucking-news/trucking-industry/trucking-is-getting-more-expensive-atri-report-explains-why
- EIA Gasoline and Diesel Fuel Update (weekly diesel) — https://www.eia.gov/petroleum/gasdiesel/ (the $6.38 value was confirmed through a compilation of EIA data. Check the EIA table directly when updating.)
- FMCSA hours-of-service rules — 49 CFR Part 395
