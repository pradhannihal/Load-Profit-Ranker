# Dad Interview (M0)

Interview date: ____ · Questions from `docs/formula.md` §8 · ~1 h

> Before you start: ask him to bring rate cons, fuel receipts or fuel-card statements, and his
> truck payment/insurance bills. Write down what he says, even "I don't know." A guess
> marked as a guess is better than a placeholder.

## Answers

| # | Question | Answer | Sets (formula field) |
|---|---|---|---|
| 1 | Own authority, leased on, or company driver? If leased: % of the line haul, and how is the fuel surcharge paid? **If he's a company driver paid per mile, stop and rethink the app.** | | `payoutPercent` |
| 2 | Real MPG, loaded vs. empty | loaded: ___ · empty: ___ | `mpg` |
| 3 | Monthly fixed costs: truck payment ___ · insurance ___ · permits/plates ___ · ELD ___ · phone ___ · parking ___ · other ___ | **total: ___** | `monthlyFixedCosts` |
| 4 | Maintenance + tires per year ÷ miles per year | maint: ___/yr · tires: ___/yr · miles: ___/yr | `maintenancePerMile`, `tiresPerMile` |
| 5 | Fuel card discount? Which region does he mostly fuel in? | | `dieselPrice` override, `fuelRegion` |
| 6 | Days actually worked per month | | `workingDaysPerMonth` |
| 7 | When he finishes a load midday, is the day done or does he keep rolling? | | `daysRoundingMode` |
| 8 | Typical dock wait at his usual shippers/receivers | | `dockWaitHours` default |
| 9 | **How does he decide yes/no on a load today?** (ask this *before* explaining the app) | | (his rule to compare against) |
| 10 | 70/8 or 60/7? Does he use the 34-hr restart? | | `cycleHoursRemaining` rules |
| 11 | Lowest profit per day he'd accept | | `targetProfitPerDay` |

Project questions (PLAN §8): Does he pay for DAT or Truckstop? ___ · Would his contacts be OK entering their cost numbers? ___

## 3 real past loads (the M0 test)

Pick loads where he remembers how they turned out: one good, one bad, one so-so.

| Field | Load 1 | Load 2 | Load 3 |
|---|---|---|---|
| Start location (where the truck was) | | | |
| `pickupLocation` → `dropoffLocation` | | | |
| `postedRate` ($) | | | |
| `loadedMiles` | | | |
| `deadheadMiles` | | | |
| `pickupDate` / `deliveryDate` | | | |
| Dock wait (h), tolls ($) | | | |
| Cycle hours left at the start | | | |
| **His verdict back then** (good / bad / ok) | | | |
| Formula profit/day (worked out on paper) | | | |
| Agree? If not, why? | | | |
