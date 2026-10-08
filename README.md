# Haul Math (Load Profit Ranker)

A phone-first web app that ranks 2–3 load offers, or checks one against a target, by
**profit per day of truck time**. It uses an owner-operator's real costs and this week's diesel price.
Built for my dad and a few of his trucking contacts.

The board rate a broker advertises (`$3.80/mi`) can hide a load that ties up the truck for 3 days.
Haul Math shows what's actually left per day, and why one load beats another.

> **Status:** Release 1, running locally (no AWS yet). The defaults are placeholders until Dad's
> real numbers are in (see `docs/dad-interview.md`). **Estimates only, not financial advice.**

## How the math works
Everything is in [`docs/formula.md`](docs/formula.md), the source of truth. In short:
`profit per day = (pay − fuel − maintenance/tires − tolls − fixed costs) ÷ days the truck is tied up`,
where days come from hours-of-service limits (incl. a 34-hr restart if needed) or the delivery
appointment, whichever is longer.

## Run it locally

You need Python 3.13 and Node 22.

**Backend** (Flask API on port 5001; macOS uses 5000 for AirPlay):
```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then paste your free EIA key into .env (never commit it)
flask --app local.app run --port 5001 --debug
```
With no key, the app still works and uses a fallback diesel price.

**Frontend** (in a second terminal):
```bash
cd frontend
npm install
npm run dev -- --host
```
Open http://localhost:5173. To use it **on a phone**, put the phone on the same Wi-Fi, open
`http://<your-laptop-ip>:5173` (Vite prints it as "Network"), then use Share → **Add to Home Screen**.
The phone only talks to Vite, which forwards `/api` to Flask.

**Tests and lint:**
```bash
cd backend && pytest && ruff check . && ruff format --check .
cd frontend && npm run lint && npm run build
```
CI runs all of these on every pull request.

## Layout
```
backend/core/       pure Python engine: config, models, validation, engine, fuel (no network, no clock)
backend/handlers/   JSON <-> engine mapping (the only camelCase/snake_case boundary)
backend/local/      Flask dev API + EIA fuel cache
backend/tests/      pytest, incl. every docs/formula.md §6 worked example
frontend/src/       React (Vite) + CSS Modules + Vega-Lite charts
docs/               formula, plan notes, learning log, Dad interview sheet
```

## Configuration & secrets
| Value | Where |
|---|---|
| EIA API key | `backend/.env` (gitignored). In AWS later: SSM Parameter Store |
| Truck settings | The phone's browser storage only. Use Settings → Backup to keep a copy |

## Roadmap
See [`PLAN.md`](PLAN.md): R1.5 adds routed miles, and R2 adds accounts on AWS.
What I learned: [`docs/learning-log.md`](docs/learning-log.md).
