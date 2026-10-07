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
