# Load Margin — Project Plan

> A phone-first web app that tells an owner-operator trucker whether a load is
> worth taking, based on **his own cost per mile** and current diesel prices.
> Built for my dad and a few of his trucking contacts.

Status: planning · Last updated: 2026-10-04 · Source spec: `trucker-app-prompt.md` (Session 1 notes)

---

## 0. Honest problems up front

1. **Time doesn't fit the original scope.** 8 weeks × 5–8 h = 40–64 hours. The full v1
   (Cognito login + saved profiles + load history + IaC + CI) is ~55 h when everything
   goes right, and realistically 75–85 h for a first AWS build. **Fix:** ship in two
   releases. Release 1 (~week 5) is a deployed calculator with no login. Release 2
   (~week 8, with 2 weeks of buffer) adds accounts. Dad gets value at week 5 even if
   Release 2 slips.
2. **Five learning goals at once** (AWS, React, IaC, testing/CI, DynamoDB) is a lot.
   That's OK only because each one is kept to its *minimum useful slice* (see each
   milestone). Going deep on any one of them is post-MVP.
3. **There is no free freight-rate API.** Lane-level spot rates are what DAT,
   Truckstop, and Greenscreens sell. v1 doesn't compare to market rates. It answers
   "does this load make *me* money?", which is the more useful question anyway.
   (Verify this firsthand in M0. Don't take it on faith.)
4. **The formula is the gate.** Nothing gets built until M0 is done. If the math is
   wrong, a nice frontend just shows wrong numbers faster.
5. **People will make money decisions with this.** It needs a visible breakdown
   ("here's how we got this number") and a plain disclaimer. A bare verdict isn't enough.

---

## 1. MVP scope

### Release 1 — "The Calculator" (target: end of week 5, tag `v0.1`)
- Cost profile form: truck MPG, fixed costs, variable costs. Exact fields are decided
  in M0. Saved **only on the device** (browser localStorage), with no account.
- Load form: pay, loaded miles, deadhead miles, plus whatever M0 says decides a load.
  Goal: **≤ 30 seconds to enter while a broker is on the phone.**
- Current diesel price for the user's region, pulled weekly from EIA. Shows an
  "as of <date>" label, and the user can type in their own pump price instead.
- Result: profit, profit per mile, and the decision metric from M0 (likely profit
  per hour), with a line-by-line breakdown.
- Works on a phone browser and can be added to the home screen.

### Release 2 — "Accounts" (target: end of week 8, buffer to week 10, tag `v1.0`)
- Sign up / log in / password reset with Cognito managed login (no hand-rolled auth).
- Cost profile stored server-side per user, imported from the phone on first login.
- Save loads, plus a load history list (newest first) that can delete entries.
- Each user sees **only** their own data, enforced by the data model.
- Onboard Dad + 2–5 contacts.

### Explicitly deferred (not v1)
| Deferred | Why / when to revisit |
|---|---|
| Market rate comparison | No free lane-level data. Revisit only if Dad already pays for DAT and wants it side by side. |
| Auto mileage (routing API) | Truck routing APIs cost money. Dad already gets miles from the broker or rate con. |
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
| Frontend | **React + JavaScript, Vite** | You've used React; Vite is the simplest modern setup. JS (not TS) keeps the number of new things down. | **Next.js**: server rendering needs a running server and adds concepts this static app doesn't need. |
| Styling | Plain CSS (or a classless CSS file like Pico.css) | Big tap targets and readable numbers are what matter in a truck cab. | Tailwind / component libraries: time spent learning them isn't time spent on the goals. |
| Frontend hosting | **S3 + CloudFront** | Static files, ~$0, and you learn how the pieces actually work. | **Amplify Hosting**: easier, but it hides the parts you want to learn. |
| Backend | **Python Lambda behind API Gateway HTTP API** | Matches your Python skills; costs nothing when idle; HTTP API has a built-in JWT authorizer for R2. | **Flask on EC2/App Runner**: always-on cost and servers to patch. (API Gateway *REST* API: more config, higher cost, no benefit here.) |
| Local backend | **Flask** as a thin dev adapter | Instant feedback loop. Same core code as Lambda. | `sam local` (needs Docker, slower loop). |
| Core logic | **Plain Python package** (`core/`), no AWS imports | Unit-tested in milliseconds; portable between Flask and Lambda. | Writing logic inside Lambda handlers: untestable and locked to AWS. |
| Database | **DynamoDB, on-demand, single table** | Scales to zero; partition-by-user enforces data isolation. | **RDS Postgres**: runs (and bills) 24/7 for a few hundred rows. |
| Auth (R2) | **Cognito User Pool + managed login** | Don't hand-roll auth. Free at this scale (verify). | **Auth0/Clerk**: fine products, but outside the AWS learning goal and another vendor. |
| Frontend auth lib | `react-oidc-context` (OIDC with Cognito) | Small; standard OIDC; it's in AWS's own Cognito React sample. | **Amplify JS Auth**: heavy and magic-heavy for one login button. |
| Infra as code | **AWS SAM** (`template.yaml`) | YAML close to CloudFormation, first-class Python Lambda support, one `sam deploy`. | **CDK**: another abstraction to learn on top of CloudFormation. Terraform: state management overhead. |
| Scheduled job | **EventBridge Scheduler → Lambda** (weekly) | Keeps EIA off the user's request path. | Calling EIA live on each request: slow, fragile, rate-limit risk. |
| Secrets | **SSM Parameter Store SecureString** | Free (standard tier). | **Secrets Manager**: ~$0.40/secret/month for rotation you don't need. |
| Tests / CI | **pytest + ruff**, GitHub Actions on every PR | Proves the money math; cheap habit to start early. | No CI ("I'll run tests myself"): you won't, at 1 a.m. before a deploy. |

---

## 3. Architecture

### Release 1 (no login)
```
 Phone browser (React, profile in localStorage)
     │  static files                      │  JSON (no auth)
     ▼                                    ▼
 CloudFront ── S3 bucket          API Gateway HTTP API  (throttled: ~5 req/s)
                                     ├── GET  /fuel?region=…  ─┐
                                     └── POST /calculate      ─┤
                                                               ▼
                                            Lambda (adapter → core/ Python)
                                                               │ read
                                                               ▼
 EventBridge Scheduler (weekly, Tue) ──► Lambda fuel_refresh ──► DynamoDB
                                             │                   (FUEL#<region>)
                                             └──► EIA API v2 (key from SSM)
```
- `/calculate` is **stateless**: the browser sends the profile and the load, and the server
  computes and returns the breakdown. No user data is stored on the server in R1,
  so no auth is needed yet.
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
New routes: `GET/PUT /me/profile`, `GET/POST /me/loads`, `DELETE /me/loads/{id}`.
**The user id comes from the verified token's `sub`, never from the URL, query, or body.**

### DynamoDB single-table design
| PK | SK | Item |
|---|---|---|
| `FUEL#PADD1C` | `2026-10-06` | weekly diesel price, source series id, fetched_at |
| `USER#<sub>` | `PROFILE` | cost profile fields (from M0) |
| `USER#<sub>` | `LOAD#<iso-timestamp>#<shortid>` | load inputs + computed result snapshot |

Access patterns: latest fuel price for a region (query PK, newest SK, limit 1) ·
my profile (get) · my loads newest-first (query PK, SK begins_with `LOAD#`, reverse).
A user query can only touch its own partition, so another trucker's rows can't come back.

Store the **computed result snapshot** with each load, so history doesn't change
when the profile or diesel price changes later.

---

## 4. Data sources & external services

| Source | Used for | Cost | Rate limits | Reliability / data quality |
|---|---|---|---|---|
| **EIA Open Data API v2**: weekly retail on-highway diesel (No. 2), by PADD region | Fuel cost | Free; needs a free API key (email signup) | Not tightly published; heavy use gets throttled. We make **~1 call/week**, so this is a non-issue. | Government source, generally stable. Published weekly (usually Monday afternoon ET, later after federal holidays; can pause during shutdowns). **It's a regional average, not his pump price**, and fuel-card discounts can be $0.10–0.50+/gal off, hence the manual override. Virginia is in PADD 1C (Lower Atlantic). |
| Freight rate benchmarks (DAT, Truckstop, Greenscreens) | Not used in v1 | Paid, hundreds of $/mo | — | M0 task: confirm firsthand that no free lane-level source exists. Free aggregates (FRED, BTS, USDA truck rate reports) show market direction, not lane prices. |
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
| 1 | Formula is wrong or misses real costs | Data quality | M0 gate: validate the formula against **3 real past loads** where Dad knows the outcome. Those become the first pytest cases. |
| 2 | Semester crunch (midterms, finals) blows the timeline | Schedule | Two releases; R1 is useful by itself; 2 weeks of buffer; cut list in §6. |
| 3 | Surprise AWS bill | Cost | Budget alerts at $5 and $10 **before deploying anything**. No VPC/NAT Gateway, no RDS. CloudWatch log retention 14 days. API throttling on the public R1 endpoints. |
| 4 | Free-plan account closure | Cost / ops | Month-5 calendar reminder to upgrade to the Paid plan (budget alerts still apply). |
| 5 | Cognito setup rabbit hole (callback URLs, CORS, tokens) | Technical / skill gap | Do auth in a separate **dev stack** first; use managed login (no custom UI); timebox to 6 h, then ask for help. |
| 6 | IDOR: one user reads another's data | Security | `sub` from the token only; `USER#<sub>` partition key; an explicit test that user B gets 404/empty for user A's load id. |
| 7 | EIA price ≠ what Dad pays; data up to ~1 week old | Data quality | Show the "as of" date; manual pump-price override; warn if the cached price is > 10 days old. |
| 8 | iPhone Safari clears localStorage after ~7 days without a visit (R1) | Technical | Tell users to "Add to Home Screen" (exempt from the 7-day rule); a "copy my profile" backup button; R2 moves the profile to the server. |
| 9 | Too slow or fiddly to use while a broker is on the phone | Adoption | Profile entered once; load form has ≤ 4 fields; time Dad on a real call in M3. |
| 10 | AI writes code you can't explain | Skill gap | Working agreement: attempt first, then ask. You write `core/` yourself. Each milestone ends with "explain it back" (README section in your own words). |
| 11 | API key or AWS credentials pushed to GitHub | Security | §7 rules: `.gitignore`, `.env.example`, SSM, GitHub push protection, no long-lived access keys. |
| 12 | Contacts trust a wrong number and lose money | Trust | Show the breakdown, put a one-line disclaimer under results, and ask contacts for feedback in the first two weeks. |

---

## 6. Build order (milestones)

Hours are estimates for focused time. Each milestone ends with something you can
**test** and a short "explain it back" note in `docs/learning-log.md`.

### M0 — The gate: formula + talking to Dad (week 1, ~4 h)
- Attempt the profit formula blanks from the Session 1 notes **without looking things up**.
  Wrong answers are welcome. Then review with Claude (the two held-back gaps get revealed here).
- Interview Dad (~1 h): real MPG, fixed costs and how to spread them per mile,
  variable costs, how deadhead counts, **how he currently decides yes/no**, whether he
  pays for DAT/Truckstop, whether he uses a fuel card discount, where he usually fuels.
- Firsthand check: confirm EIA diesel data is reachable and that no free lane-rate API exists.
- Output: `docs/formula.md` (final formula + field list) and `docs/dad-interview.md`.
- ✅ **Test:** run 3 of Dad's real past loads through the formula on paper. Dad agrees with each verdict, or you understand why not.

### M1 — Repo + core math + CI (weeks 1–2, ~5 h)
- `git init`, GitHub repo, `.gitignore`, README skeleton, branch workflow (§7).
- `backend/core/margin.py`: pure functions, no AWS imports. **You write this one.**
- pytest: the 3 real loads + edge cases (zero miles, huge deadhead, negative profit).
- GitHub Actions: ruff + pytest on every PR.
- ✅ **Test:** `pytest` passes locally and the CI check is green on a PR.

### M2 — Fuel data + local API (weeks 2–3, ~6 h)
- EIA key; explore the API in a scratch script; find the series id for your region.
- `core/fuel.py` (parse/validate EIA response) + `handlers/fuel_refresh.py` logic.
- Local Flask app: `GET /fuel`, `POST /calculate`, both thin adapters over `core/`.
- ✅ **Test:** `curl localhost:5000/calculate` with a real load returns the same numbers as M0's paper version.

### M3 — React frontend, local (weeks 3–4, ~8 h)
- Vite + React (JS). Screens: Profile (localStorage), New Load, Result breakdown.
- Mobile-first: big inputs, numeric keyboards (`inputmode="decimal"`), readable in sunlight.
- ✅ **Test:** run `vite --host` and open it on Dad's phone over home Wi-Fi. He enters a real load during (or right after) a broker call in under 30 s.

### M4 — First AWS deploy → **Release 1** (weeks 4–5, ~10 h)
- AWS account: root MFA, **budget alerts $5/$10 first**, an admin user via IAM Identity Center (no root use, no long-lived keys).
- EIA key → SSM SecureString.
- SAM `template.yaml`: DynamoDB table, `calculate` + `fuel` Lambdas, `fuel_refresh` Lambda + weekly schedule, HTTP API with throttling + CORS, S3 + CloudFront (Origin Access Control) for the frontend.
- Deploy a **dev** stack, then a **prod** stack (`samconfig.toml` environments).
- ✅ **Test:** Dad uses the CloudFront URL from his phone for one real week. The fuel price updates by itself after the scheduled run. Tag `v0.1`.

### M5 — Auth (weeks 6–7, ~10 h)
- Cognito User Pool + app client + managed login (in the dev stack first).
- HTTP API JWT authorizer on `/me/*` routes. The handler reads `sub` from claims.
- Frontend: `react-oidc-context` login/logout, attach the token to API calls.
- ✅ **Test:** two test accounts. Each can log in, reset a password, and call `/me/profile`. A request with no token or a bad one gets 401 **before** Lambda runs (check the logs).

### M6 — Saved profile + load history (weeks 7–8, ~8 h)
- `/me/profile` GET/PUT; `/me/loads` GET/POST; `DELETE /me/loads/{id}`.
- One-time "import profile from this device" after first login.
- ✅ **Test:** save a load on your phone and see it on your laptop. The IDOR test: account B can't read or delete account A's load by id (automated test + manual try).

### M7 — Harden + onboard → **Release 2** (weeks 9–10 buffer, ~6 h)
- CloudWatch alarm on Lambda errors → email you. Log retention set. Disclaimer text.
- Short user guide (in the README or one page in the app). Onboard Dad + 2–5 contacts by phone.
- ✅ **Test:** every contact signs up by themselves and runs one real load. Collect feedback in `docs/ideas.md`. Tag `v1.0`.

**Total ≈ 57 h** over 8–10 weeks.
**Cut list if behind (in order):** custom styling polish → CloudWatch alarm (check logs by hand) → load delete → profile import (re-type it) → push R2 past finals. **Never cut:** M0, tests for `core/`, budget alerts, the IDOR test.

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
│   ├── formula.md                  # M0 output, source of truth for the math
│   ├── dad-interview.md
│   ├── learning-log.md             # "explain it back" notes per milestone
│   ├── ideas.md                    # feature requests parking lot
│   └── decisions/                  # short ADRs: 0001-dynamodb-over-rds.md, ...
├── backend/
│   ├── core/                       # pure Python: margin.py, fuel.py — no AWS
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
1. **The formula**: resolved in M0. What decides a load for Dad: profit per mile, per hour, or per day? How are hours estimated?
2. Does Dad already pay for DAT or Truckstop? If yes, he sees market rates there, and the "market comparison" stretch goal may not be needed.
3. Does Dad use a fuel card discount, and where does he usually fuel (sets the default EIA region)?
4. How should fixed costs be spread per mile: last year's actual miles, or a planned annual figure?
5. Are the contacts comfortable entering their cost numbers into an app a college student runs? (Affects the disclaimer, a privacy note, and whether to offer data deletion.)
6. Custom domain after R2: yes or no? (Budget allows it.)
7. Long-term ownership: whose AWS account and card; what happens during summer break or if you stop maintaining it.
8. When to start the v2 expense tracker: after R2 feedback, not before.

## 9. Working agreement (carried from the spec)
Architect/mentor mode: teach the concept first, attempt before code is shown,
explain *why* each step comes where it does, push back on scope creep and on plans
that won't survive real data, and ask instead of guessing.
