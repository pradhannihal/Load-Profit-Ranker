# Load Profit Ranker — Project Plan

> A phone-first web app that ranks 2–3 load offers (or checks one against a
> target) by **profit per day of truck time**, using an owner-operator's real
> costs and current diesel prices. Built for my dad and a few of his trucking contacts.

Status: M1–M3 built locally (placeholder defaults; M0 interview pending) · Last updated: 2026-10-07 · Source spec: `trucker-app-prompt.md` (Session 1 notes)
**The math lives in [`docs/formula.md`](docs/formula.md). It's the source of truth. If this plan and the formula disagree, the formula wins.**

---

## 0. Honest problems up front

1. **Time doesn't fit the original scope.** 8 weeks × 5–8 h = 40–64 hours. The full v1
   (Cognito login + saved settings + comparison history + IaC + CI) is ~55 h when everything
   goes right, and realistically 75–85 h for a first AWS build. **Fix:** ship in two
   releases. Release 1 (~week 5) is a deployed calculator with no login. Release 2
   (~week 8, with 2 weeks of buffer) adds accounts. Dad gets value at week 5 even if
   Release 2 slips.
2. **Five learning goals at once** (AWS, React, IaC, testing/CI, DynamoDB) is a lot.
   That's OK only because each one is kept to its *minimum useful slice* (see each
   milestone). Going deep on any one of them is post-MVP.
3. **There is no free freight-rate API that can price any lane.** Lane-level spot rates are what DAT,
   Truckstop, and Greenscreens sell. Free tiers (e.g. Freight Data Watch) cover only major
   corridors, from vague sources (checked in M0, see `docs/learning-log.md`). v1 doesn't compare to market rates. It answers
   "does this load make *me* money?", which is the more useful question anyway.
4. **The formula is the gate.** It's drafted in `docs/formula.md`, but its
   defaults are placeholders (ATRI fleet averages, a made-up $5,000/month fixed
   cost). Nothing gets built until Dad's real numbers are in and the 3-real-loads
   test passes. If the math is wrong, a nice frontend just shows wrong numbers faster.
5. **People will make money decisions with this.** It needs a visible breakdown
   ("here's how we got this number") and a plain disclaimer. A bare verdict isn't enough.

---

## 1. MVP scope

### Release 1 — "The Ranker" (target: end of week 5, tag `v0.1`)
All fields and math come from `docs/formula.md` §3–§5.
- **Truck settings** (formula §3c): MPG, fuel region, per-mile costs, monthly fixed
  costs, payout %, rounding mode, optional target $/day. Saved **only on the device**
  (browser localStorage), with no account. Results are blocked until monthly fixed
  costs are entered.
- **Trip context** at the top of the compare screen (formula §3a): current location,
  available date (default today), hours left on the 70-hr cycle (from the ELD).
- **Up to 3 load cards** (formula §3b): rate, **typed** loaded and deadhead miles,
  optional dates, dock wait, tolls. Goal: **≤ 30 seconds per load while a broker is
  on the phone.**
- Diesel price for Dad's region, pulled weekly from EIA. Shows an "as of <date>"
  label; a manual pump/fuel-card price overrides it.
- **Results:** loads ranked by profit/day (tie-breaker profit/mile), the winner and
  "why it won" (per-day line comparison), "Loses money" flag, target met/missed,
  warnings ("needs a 34-hr restart", "may not make this pickup"), board rate vs.
  true profit per mile, and the full cost breakdown.
- Works on a phone browser and can be added to the home screen.

### Release 1.5 — "Routing" (target: ~week 6, tag `v0.2`)
- Dad types cities; the app fills in loaded and deadhead miles using OpenRouteService
  truck routing + geocoding. Called from a Lambda (key in SSM), never from the browser.
- Typed miles always override routed miles. Show which route was used.
- First thing to cut if behind: typed miles keep working without it.

### Release 2 — "Accounts" (target: end of week 8, buffer to week 10, tag `v1.0`)
- Sign up / log in / password reset with Cognito managed login (no hand-rolled auth).
- Truck settings stored server-side per user, imported from the phone on first login.
- Save **comparisons** (inputs + ranked results), plus a history list (newest first) that can delete entries.
- Each user sees **only** their own data, enforced by the data model.
- Onboard Dad + 2–5 contacts.

### Explicitly deferred (not v1)
| Deferred | Why / when to revisit |
|---|---|
| Market rate comparison | No free lane-level data. Revisit only if Dad already pays for DAT and wants it side by side. |
| Broker grade / risky-broker deduction | No sourced percentages; slows entry (formula §7). Later: one "risky broker" checkbox. |
| Terrain MPG penalty | Unsourced. Later: separate loaded vs. empty MPG from Dad's fuel records. |
| Worst-case delay "High Risk" flag | v1.1, once Dad's real delay experience sets the hours. |
| Round-trip / outbound market proxy | Needs load board data. Later: Dad tags the drop-off market strong/average/weak. |
| Expense tracker / logbook (v2 idea) | The natural next step ("tracker feeds the calculator"), but it's a separate project. |
| Teams, sharing, roles, admin panel, avatars | Build only if people are actually using it and ask. |
| Native app / app stores | A web app added to the home screen is enough. |
| Custom domain | ~$15/yr + Route 53 $0.50/mo fits the budget. Add after R2 if the CloudFront URL bugs Dad. |
| CI auto-deploy (GitHub OIDC) | Deploy manually with `sam deploy` until it's worth automating. |
| Frontend tests (Vitest), TypeScript | Post-MVP learning goals. |
| IFTA, fuel-tax, per-state anything | Scope creep. |

**Scope rule:** a new feature gets in only if Dad (or a contact) asks for it twice
*after* using the app. Write requests in `docs/ideas.md` instead of building them.

---

## 2. Tech stack

| Layer | Choice | Why | Rejected alternative |
|---|---|---|---|
| Charts | **Vega-Lite** (`vega-embed`, lazy-loaded) | Declarative specs; 4 charts: profit/day, where the money goes, board vs true $/mi, days used. | Recharts/Chart.js: imperative or React-specific; Vega-Lite specs are portable. |
| Frontend | **React + JavaScript, Vite** | You've used React; Vite is the simplest modern setup. JS (not TS) keeps the number of new things down. | **Next.js**: server rendering needs a running server and adds concepts this static app doesn't need. |
| Styling | **CSS Modules** (built into Vite), highway road-sign look; app name **Haul Math** | Big tap targets and readable numbers are what matter in a truck cab. Styles are scoped per component. | Tailwind / component libraries: time spent learning them isn't time spent on the goals. |
| Frontend hosting | **S3 + CloudFront** | Static files, ~$0, and you learn how the pieces actually work. | **Amplify Hosting**: easier, but it hides the parts you want to learn. |
| Backend | **Python Lambda behind API Gateway HTTP API** | Matches your Python skills; costs nothing when idle; HTTP API has a built-in JWT authorizer for R2. | **Flask on EC2/App Runner**: always-on cost and servers to patch. (API Gateway *REST* API: more config, higher cost, no benefit here.) |
| Local backend | **Flask** as a thin dev adapter | Instant feedback loop. Same core code as Lambda. | `sam local` (needs Docker, slower loop). |
| Core logic | **Plain Python package** (`core/`), no AWS imports | Unit-tested in milliseconds; portable between Flask and Lambda. | Writing logic inside Lambda handlers: untestable and locked to AWS. |
| Database | **DynamoDB, on-demand, single table** | Scales to zero; partition-by-user enforces data isolation. | **RDS Postgres**: runs (and bills) 24/7 for a few hundred rows. |
| Auth (R2) | **Cognito User Pool + managed login** | Don't hand-roll auth. Free at this scale (verify). | **Auth0/Clerk**: fine products, but outside the AWS learning goal and another vendor. |
| Frontend auth lib | `react-oidc-context` (OIDC with Cognito) | Small; standard OIDC; it's in AWS's own Cognito React sample. | **Amplify JS Auth**: heavy and magic-heavy for one login button. |
| Infra as code | **AWS SAM** (`template.yaml`) | YAML close to CloudFormation, first-class Python Lambda support, one `sam deploy`. | **CDK**: another abstraction to learn on top of CloudFormation. Terraform: state management overhead. |
| Routing (R1.5) | **OpenRouteService** directions + geocoding (truck/HGV profile), called server-side | Free API key and a truck profile. | **Google Maps Directions**: no truck routing, and it needs billing set up. |
| Scheduled job | **EventBridge Scheduler → Lambda** (weekly) | Keeps EIA off the user's request path. | Calling EIA live on each request: slow, fragile, rate-limit risk. |
| Secrets | **SSM Parameter Store SecureString** | Free (standard tier). | **Secrets Manager**: ~$0.40/secret/month for rotation you don't need. |
| Tests / CI | **pytest + ruff**, GitHub Actions on every PR | Proves the money math; cheap habit to start early. | No CI ("I'll run tests myself"): you won't, at 1 a.m. before a deploy. |

---

## 3. Architecture

### Release 1 (no login)
```
 Phone browser (React, truck settings in localStorage)
     │  static files                      │  JSON (no auth)
     ▼                                    ▼
 CloudFront ── S3 bucket          API Gateway HTTP API  (throttled: ~5 req/s)
                                     ├── GET  /fuel?region=…  ─┐
                                     ├── POST /rank           ─┤
                                     └── POST /route  (R1.5)  ─┤──► OpenRouteService
                                                               ▼
                                            Lambda (adapter → core/ Python)
                                                               │ read
                                                               ▼
 EventBridge Scheduler (weekly, Tue) ──► Lambda fuel_refresh ──► DynamoDB
                                             │                   (FUEL#<region>)
                                             └──► EIA API v2 (key from SSM)
```
- `/rank` is **stateless**: the browser sends `{tripContext, truckSettings, loads[≤3]}`,
  and the server returns ranked results with breakdowns and warnings. No user data
  is stored on the server in R1, so no auth is needed yet.
- The fuel lookup uses `truckSettings.fuelRegion`.
- **Naming:** Python uses snake_case (PEP 8). JSON uses formula.md's camelCase names
  (`deadheadMiles`), so the doc maps 1:1 to the API. Converting between the two
  happens in exactly one place: the handler adapter.
- Calling EIA happens **only** in the scheduled job. Users always read the cached
  price, so the app keeps working when EIA is down.

### Release 2 (adds accounts)
```
 Browser ──login──► Cognito managed login ──► ID/access token (JWT)
    │
    └── request + JWT ──► API Gateway (JWT authorizer rejects bad tokens)
                              │  claims.sub = user id
                              ▼
                          Lambda ──► DynamoDB  PK = USER#<sub>
```
New routes: `GET/PUT /me/settings`, `GET/POST /me/comparisons`, `DELETE /me/comparisons/{id}`.
**The user id comes from the verified token's `sub`, never from the URL, query, or body.**

### DynamoDB single-table design
| PK | SK | Item |
|---|---|---|
| `FUEL#PADD1C` | `2026-10-06` | weekly diesel price, source series id, fetched_at |
| `USER#<sub>` | `SETTINGS` | truck settings (formula §3c) |
| `USER#<sub>` | `COMPARISON#<iso-timestamp>#<shortid>` | trip context + loads + ranked result snapshot |

Access patterns: latest fuel price for a region (query PK, newest SK, limit 1) ·
my settings (get) · my comparisons newest-first (query PK, SK begins_with `COMPARISON#`, reverse).
A user query can only touch its own partition, so another trucker's rows can't come back.

Store the **ranked result snapshot** with each comparison, so history doesn't change
when settings or the diesel price change later.

---

## 4. Data sources & external services

| Source | Used for | Cost | Rate limits | Reliability / data quality |
|---|---|---|---|---|
| **EIA Open Data API v2**: weekly retail on-highway diesel (No. 2), by PADD region | Fuel cost | Free; needs a free API key (email signup) | Not tightly published; heavy use gets throttled. We make **~1 call/week**, so this is a non-issue. | Government source, generally stable. Published weekly (usually Monday afternoon ET, later after federal holidays; can pause during shutdowns). **It's a regional average, not his pump price**, and fuel-card discounts can be $0.10–0.50+/gal off, hence the manual override. Virginia is in PADD 1C (Lower Atlantic). |
| Freight rate benchmarks (DAT, Truckstop, Greenscreens) | Not used in v1 | Paid, hundreds of $/mo | — | Checked in M0 (2026-10-06): Freight Data Watch has a free tier (100 req/day) for major corridors only, with vague sources. Free aggregates (FRED, BTS, USDA truck rate reports) show market direction, not lane prices. |
| **OpenRouteService** (R1.5): directions (driving-hgv) + geocoding | Loaded and deadhead miles | Free; needs a free API key | Free tier ≈ 2,000 directions/day and ≈ 1,000 geocodes/day, plus per-minute caps (verify). One comparison ≈ 4 geocodes + 6 routes. | Run by HeiGIT (non-profit), OpenStreetMap data. Routed miles ≠ the broker's "practical miles" (PC*MILER), hence the manual override. |
| **ATRI** *Operational Costs of Trucking, 2026* | Default maintenance ($0.215/mi) and tire ($0.050/mi) costs | Free report | — | Fleet-wide averages. Small fleets run higher. Replace with Dad's numbers. |
| AWS Cognito | Auth (R2) | Free tier covers far more than 5 users (verify current MAU terms) | Default email sending is limited (~50 emails/day), plenty for 5 users | Managed; the managed login UI is plain but works. |
| AWS (Lambda, HTTP API, DynamoDB, S3, CloudFront, Scheduler, SSM) | Everything else | Estimated **< $1/month** at this usage | API Gateway throttling we set ourselves | Managed services. |

**Estimated monthly cost:** ~$0–1. Optional domain later: +~$1.75/mo. Well under the $10 budget.

> ⚠️ AWS changed its free tier in July 2025. New accounts choose a **Free plan**
> (credits, time-limited, ~6 months) or a **Paid plan**. On the Free plan, the
> account can be **closed when it expires unless you upgrade**. Read the current
> terms at signup, and put a calendar reminder at month 5 to upgrade. Otherwise
> Dad's app disappears.

---

## 5. Risks

| # | Risk | Type | Mitigation |
|---|---|---|---|
| 1 | Formula is wrong or misses real costs | Data quality | M0 gate: validate the formula against **3 real past loads** where Dad knows the outcome. Those become pytest cases alongside the formula §6 fixtures. |
| 1b | Placeholder defaults treated as real (ATRI averages, $5,000 fixed, 6.5 MPG) | Data quality | No silent default for monthly fixed costs (results blocked until entered); an "estimate" badge on every unverified default in settings. |
| 1c | HOS model too simple (formula §7b) | Data quality | Documented simplifications; check them against Dad's real trips in M0; the 70-hr cycle and 34-hr restart are already modeled. |
| 1d | Routed miles differ from broker miles (R1.5) | Data quality | Typed miles override; show the route used. |
| 2 | Semester crunch (midterms, finals) blows the timeline | Schedule | Two releases; R1 is useful by itself; 2 weeks of buffer; cut list in §6. |
| 3 | Surprise AWS bill | Cost | Budget alerts at $5 and $10 **before deploying anything**. No VPC/NAT Gateway, no RDS. CloudWatch log retention 14 days. API throttling on the public R1 endpoints. |
| 4 | Free-plan account closure | Cost / ops | Month-5 calendar reminder to upgrade to the Paid plan (budget alerts still apply). |
| 5 | Cognito setup rabbit hole (callback URLs, CORS, tokens) | Technical / skill gap | Do auth in a separate **dev stack** first; use managed login (no custom UI); timebox to 6 h, then ask for help. |
| 6 | IDOR: one user reads another's data | Security | `sub` from the token only; `USER#<sub>` partition key; an explicit test that user B gets 404/empty for user A's comparison id. |
| 7 | EIA price ≠ what Dad pays; data up to ~1 week old | Data quality | Show the "as of" date; manual pump-price override; warn if the cached price is > 10 days old. |
| 8 | iPhone Safari clears localStorage after ~7 days without a visit (R1) | Technical | Tell users to "Add to Home Screen" (exempt from the 7-day rule); a "copy my settings" backup button; R2 moves settings to the server. |
| 9 | Too slow or fiddly to use while a broker is on the phone | Adoption | Settings entered once; trip context remembers the last values; only rate + miles are required per load; time Dad on a real call in M3. |
| 10 | AI writes code you can't explain | Skill gap | Working agreement: attempt first, then ask. You write `core/` yourself. Each milestone ends with "explain it back" (README section in your own words). |
| 11 | API key or AWS credentials pushed to GitHub | Security | §7 rules: `.gitignore`, `.env.example`, SSM, GitHub push protection, no long-lived access keys. |
| 12 | Contacts trust a wrong number and lose money | Trust | Show the breakdown, put a one-line disclaimer under results, and ask contacts for feedback in the first two weeks. |

---

## 6. Build order (milestones)

Hours are estimates for focused time. Each milestone ends with something you can
**test** and a short "explain it back" note in `docs/learning-log.md`.

### M0 — The gate: formula + talking to Dad (week 1, ~4 h)
- ✅ Formula drafted: `docs/formula.md` (rev 2: profit per day, trip context, 70-hr cycle, target, warnings).
- Interview Dad (~1 h) using formula §8. Replace the placeholder defaults with his real numbers.
- ✅ Firsthand check: EIA diesel is reachable for PADD 1C ($5.699, 2026-10-05); no free source can price any lane (see `docs/learning-log.md`).
- Output: updated `docs/formula.md` + `docs/dad-interview.md`.
- ✅ **Test:** run 3 of Dad's real past loads through the formula on paper. Dad agrees with each verdict, or you understand why not.

### M1 — Repo + engine + CI (weeks 1–2, ~7 h) ✅ PR #4
- ✅ GitHub repo exists. Still to do: `.gitignore`, README skeleton, branch protection (§7).
- `backend/core/`, pure Python with no AWS imports, no network, no clock. **You write this.**
  - `config.py`: frozen `EngineConfig` dataclass holding every constant and default (formula §3d + defaults from §3c).
  - `models.py`: `TripContext`, `TruckSettings`, `LoadInput`, `LoadResult`, `Ranking`.
  - `validation.py`: errors (block) vs. warnings (still ranked), one test per formula §5 row.
  - `engine.py`: `compute_load(...)` and `rank_loads(...)`, including the cycle restart, target, and "why it won".
- Floats with full precision; round only for display. Tests use `pytest.approx(abs=0.01)` (days: `abs=0.0001`).
- pytest fixtures: formula §6 worked example (fractional + whole), cycle-limit test (B drops below C), target test, plus Dad's 3 real loads from M0.
- GitHub Actions: ruff + pytest on every PR.
- ✅ **Test:** `pytest` passes locally and the CI check is green on a PR.

### M2 — Fuel data + local API (weeks 2–3, ~6 h) ✅ PR #5
- EIA key; explore the API in a scratch script; find the series id for each PADD region.
- `core/fuel.py` (parse/validate EIA response) + `handlers/fuel_refresh.py` logic.
- Local Flask app: `GET /fuel?region=…`, `POST /rank`, both thin adapters over `core/` (camelCase ↔ snake_case mapping lives here).
- ✅ **Test:** `curl localhost:5000/rank` with the formula §6 loads returns exactly the fixture numbers and ranking.

### M3 — React frontend, local (weeks 3–4, ~9 h) ✅ built; phone test with Dad pending
- Vite + React (JS). Screens: Truck settings (localStorage, "estimate" badges), Compare (trip context + up to 3 load cards), Results (ranking, winner + why it won, warnings, target, breakdown).
- Mobile-first: big inputs, numeric keyboards (`inputmode="decimal"`), readable in sunlight.
- ✅ **Test:** run `vite --host` and open it on Dad's phone over home Wi-Fi. He compares 2 real offers, entering each one in under 30 s.

### M4 — First AWS deploy → **Release 1** (weeks 4–5, ~10 h)
- AWS account: root MFA, **budget alerts $5/$10 first**, an admin user via IAM Identity Center (no root use, no long-lived keys).
- EIA key → SSM SecureString.
- SAM `template.yaml`: DynamoDB table, `rank` + `fuel` Lambdas, `fuel_refresh` Lambda + weekly schedule, HTTP API with throttling + CORS, S3 + CloudFront (Origin Access Control) for the frontend.
- Deploy a **dev** stack, then a **prod** stack (`samconfig.toml` environments).
- ✅ **Test:** Dad uses the CloudFront URL from his phone for one real week. The fuel price for his region updates by itself after the scheduled run. Tag `v0.1`.

### M4.5 — Routing → **Release 1.5** (week 6, ~6 h)
- OpenRouteService key → SSM. `core/routing.py` parses responses (pure); `handlers/route.py` calls ORS (geocode cities, then driving-hgv directions).
- `POST /route`: returns loaded + deadhead miles. The frontend fills the mile fields, and typed values override them.
- ✅ **Test:** 3 real lanes Dad knows; routed miles land within ~5% of what his rate cons say (otherwise, find out why). Tag `v0.2`.

### M5 — Auth (week 7, ~10 h)
- Cognito User Pool + app client + managed login (in the dev stack first).
- HTTP API JWT authorizer on `/me/*` routes. The handler reads `sub` from claims.
- Frontend: `react-oidc-context` login/logout, attach the token to API calls.
- ✅ **Test:** two test accounts. Each can log in, reset a password, and call `/me/settings`. A request with no token or a bad one gets 401 **before** Lambda runs (check the logs).

### M6 — Saved settings + comparison history (weeks 8–9, ~8 h)
- `/me/settings` GET/PUT; `/me/comparisons` GET/POST; `DELETE /me/comparisons/{id}`.
- One-time "import settings from this device" after first login.
- ✅ **Test:** save a comparison on your phone and see it on your laptop. The IDOR test: account B can't read or delete account A's comparison by id (automated test + manual try).

### M7 — Harden + onboard → **Release 2** (weeks 9–10, ~6 h)
- CloudWatch alarm on Lambda errors → email you. Log retention set. Disclaimer text.
- Short user guide (in the README or one page in the app). Onboard Dad + 2–5 contacts by phone.
- ✅ **Test:** every contact signs up by themselves and runs one real comparison. Collect feedback in `docs/ideas.md`. Tag `v1.0`.

**Total ≈ 66 h** over 10 weeks. That's more than the original 57 h, because the 70-hr cycle, the ranker UI, and routing all add work. The R2 buffer is now thin.
**Cut list if behind (in order):** R1.5 routing (typed miles still work) → custom styling polish → CloudWatch alarm (check logs by hand) → comparison delete → settings import (re-type it) → push R2 past finals. **Never cut:** M0, the formula fixture tests (incl. cycle-limit), budget alerts, the IDOR test.

---

## 7. GitHub setup

### Repo structure
```
ForBaba/
├── README.md
├── PLAN.md
├── .gitignore
├── .github/workflows/ci.yml        # ruff + pytest + frontend build
├── docs/
│   ├── formula.md                  # source of truth for the math (rev 2)
│   ├── dad-interview.md
│   ├── learning-log.md             # "explain it back" notes per milestone
│   ├── ideas.md                    # feature requests parking lot
│   └── decisions/                  # short ADRs: 0001-dynamodb-over-rds.md, ...
├── backend/
│   ├── core/                       # pure Python, no AWS: config, models, validation, engine, fuel, routing
│   ├── handlers/                   # Lambda adapters (~5–15 lines each)
│   ├── local/app.py                # Flask dev adapter
│   ├── tests/
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                       # Vite + React
│   ├── src/
│   └── .env.example                # VITE_API_URL=, VITE_COGNITO_* (not secrets)
└── infra/
    ├── template.yaml               # AWS SAM
    └── samconfig.toml              # dev + prod environments (no secrets)
```

### README outline
1. What it is (one paragraph + screenshot) and who it's for
2. How the math works (link `docs/formula.md`) + disclaimer
3. Architecture diagram (from PLAN §3)
4. Run locally: backend (venv, Flask), frontend (npm), tests
5. Deploy: prerequisites, `sam build && sam deploy --config-env dev|prod`, frontend upload
6. Configuration & secrets (where each value lives)
7. Cost notes + budget alerts
8. Roadmap / status (link PLAN.md)
9. What I learned (link learning-log)

### `.gitignore` (key entries)
`.env`, `.env.*`, `!.env.example`, `.venv/`, `__pycache__/`, `.pytest_cache/`,
`.ruff_cache/`, `node_modules/`, `frontend/dist/`, `.aws-sam/`, `*.pem`,
`.DS_Store`, `coverage/`, `.coverage`.

### Keeping secrets out
- **The only real secret is the EIA API key** (+ your AWS credentials). EIA key: SSM
  SecureString in AWS, `backend/.env` locally (gitignored), placeholder in `.env.example`.
- `VITE_*` variables end up **in the public JS bundle**. Only non-secret values go
  there (API URL, Cognito client id and domain).
- AWS credentials: `aws configure sso` (IAM Identity Center) gives short-lived credentials.
  **Never** create root access keys; never paste keys into code or chat.
- Turn on GitHub **secret scanning + push protection** (repo Settings → Code security).
- If a secret ever gets committed: **rotate it first**, then clean history. Deleting the line isn't enough.

### Branch workflow (solo, lightweight)
- `main` is always deployable; protect it (require PR + green CI; no force push).
- One branch per milestone or feature: `m2-fuel-api`, `fix/deadhead-rounding`.
- Small PRs with a description (what/why/how tested). Read your own diff before merging.
- Squash-merge. Tag releases: `v0.1` (R1), `v1.0` (R2).
- Deploy prod only from `main`.
- Repo visibility: **public** recommended (portfolio + free push protection). No user data lives in the repo.

---

## 8. Open questions
**Questions for Dad** (MPG, fixed costs, fuel card, region, working days, rounding, dock wait, 70/8 vs 60/7, minimum $/day, his current rule) live in [`docs/formula.md` §8](docs/formula.md). They have to be answered before the results can be trusted.

Project-level questions:
1. Does Dad already pay for DAT or Truckstop? If yes, he sees market rates there, and the "market comparison" stretch goal may not be needed.
2. Are the contacts comfortable entering their cost numbers into an app a college student runs? (Affects the disclaimer, a privacy note, and whether to offer data deletion.)
3. Custom domain after R2: yes or no? (Budget allows it.)
4. Long-term ownership: whose AWS account and card; what happens during summer break or if you stop maintaining it.
5. When to start the v2 expense tracker: after R2 feedback, not before.

## 9. Working agreement (carried from the spec)
**Changed 2026-10-07:** at Nihal's request, Claude built M1–M3 (incl. `core/`) and merges PRs once CI is green. Nihal reviews each PR and writes the "explain it back" notes in `docs/learning-log.md`. Scope-creep pushback still applies.

Architect/mentor mode: teach the concept first, attempt before code is shown,
explain *why* each step comes where it does, push back on scope creep and on plans
that won't survive real data, and ask instead of guessing.
