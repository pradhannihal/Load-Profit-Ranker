# Learning Log

"Explain it back" notes, one section per milestone (PLAN.md §6).

## M0 checks (2026-10-06)

### EIA diesel price: reachable ✅
- Endpoint: `GET https://api.eia.gov/v2/petroleum/pri/gnd/data/`
- Params: `frequency=weekly`, `data[]=value`, `facets[duoarea][]=R1Z` (PADD 1C, Lower Atlantic),
  `facets[product][]=EPD2D` (No 2 Diesel), `sort[0][column]=period`, `sort[0][direction]=desc`, `length=1`
- Series id: `EMD_EPD2D_PTE_R1Z_DPG` (retail, $/gal)
- Latest: **$5.699/gal, period 2026-10-05**. That's $0.68 below the $6.38 US-average fallback in formula.md, so the region matters.
- Codes were found through `/v2/petroleum/pri/gnd/facet/duoarea` and `/facet/product`.
- Notes for `core/fuel.py` (M2):
  - `value` is a **string** (`"5.699"`), so convert it to float and validate it (> 0).
  - Use `period` as the "as of" date, not the fetch time (PLAN risk #7).
  - EIA returns an "incomplete return" warning even with `length=1`. Ignore `warnings`; don't treat them as errors.
  - zsh: put the URL in quotes and use `curl -g`, or `[]` gets read as a glob pattern.

### Free lane-level freight rates: partly exists, still deferred
- DAT, Truckstop, and Greenscreens lane rates are still paid.
- Freight Data Watch has a free API tier (100 req/day) with "market rates & top lanes". It covers major
  corridors only (e.g. DAL→ATL), and its sources are vague ("aggregated from multiple public and
  partner data sources"). It can't price a specific lane Dad is offered.
- DAT Trendlines: free national/regional averages, not lane prices.
- Verdict: no change to v1. Market comparison stays deferred (PLAN §1).

### In my own words
<!-- Nihal: 3–5 sentences on how an EIA v2 request is built (route, data, facets, sort/length)
     and why we cache the weekly price instead of calling EIA on every /rank request. -->

## M1: engine + CI (2026-10-07)

Built by Claude; Nihal explains it back. Code: `backend/core/`, tests: `backend/tests/`.

Things worth knowing:
- **Monthly fixed costs never change the ranking.** Fixed $/day = monthly ÷ working days, the same for every
  load, so it's subtracted equally from each load's profit/day. It still matters for the *verdict*
  (target met? loses money?), which is why results are blocked without it.
- Whole-day rounding uses `ceil(round(x, 9))`, so float noise (2.0000000001) doesn't turn 2 days into 3.
- The sort is stable: exact ties keep the order the loads were entered.

### In my own words
<!-- Nihal: walk through compute_load() for Load B in the cycle-limit test (cycleHoursRemaining=20).
     Why does B fall below C? Which line of code makes that happen? -->

## M2: fuel + local API (2026-10-07)

- `handlers/mapping.py` is the only place camelCase JSON meets snake_case Python. Error `field` paths
  come back in JSON names (`loads[1].loadedMiles`) so the UI can put the message next to the right input.
- `/rank` never calls EIA. It uses the cached price (or the override, or the $6.38 fallback). Only `/fuel`
  fetches, at most once a day per region. In M4 that becomes a weekly scheduled Lambda + DynamoDB.
- The EIA URL contains the API key, so the cache logs only the error *type* on failure, never the URL.
- macOS uses port 5000 for AirPlay, so Flask runs on 5001.

### In my own words
<!-- Nihal: what happens, step by step, when the phone taps RANK? Browser -> Vite proxy -> Flask -> mapping -> engine -> back. -->

## M3: frontend (2026-10-07)

- Two screens: **Compare** (trip, diesel line, up to 3 loads, RANK, results) and **Settings**.
  Settings, the trip and the loads are saved in the phone's localStorage (`haulmath.*.v1` keys).
- All math stays on the server. The frontend only formats numbers and builds the request (`src/lib/request.js`).
- Vega-Lite charts are lazy-loaded: Vega is ~290 kB gzipped, so it downloads only when results appear.
- Chart colors come from the same CSS variables as the page, so light/dark mode switches both.
- Tested in Chrome at 375 px (iPhone width), in light and dark mode, with the §6 example: the numbers match the fixtures.

### In my own words
<!-- Nihal: why does "Re-rank" appear only after you change something? (Hint: App.jsx compares the
     request body to the one that was last ranked.) -->
