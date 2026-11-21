# timesheets

Time tracking and invoicing for freelancers: track your hours against clients
and projects, fill in a weekly timesheet, and turn unbilled time into PDF
invoices.

## Features

- **Clients and projects** with hourly rates; a project can override its
  client's rate, have an hour budget and be billable or not by default
- **Running timer** in the top bar (Alt+S), continue earlier tasks with one
  click, and stop a forgotten timer at the time you really finished
- **Manual entries**, CSV export, filters, bulk billable/delete
- **Weekly timesheet** grid where you can type hours straight into a cell
  (`1:30`, `1.5`, `90m`, `1h30`), with a weekly target
- **Rounding rules**: none, 6 minutes or 15 minutes, applied per entry (always
  up) when invoicing and valuing time; tracked time is never changed
- **Billable vs non-billable** time, per project and per entry
- **Invoices** generated from unbilled time for a client and period, grouped per
  project or per entry, with tax lines, extra lines (expenses, discounts),
  reference/PO number, notes, payment details and a PDF download
- **Invoice status**: draft, sent, paid and overdue (sent and past the due date)
- **Reports** of tracked, billable and unbilled time by client, project or month
  (CSV too), and invoiced vs paid revenue per month
- Dashboard, dark mode, keyboard shortcuts (`?`), works on a phone

Ideas for what could come next are in [ROADMAP.md](ROADMAP.md).

## Stack

| Part  | Tech                                                                   |
| ----- | ---------------------------------------------------------------------- |
| API   | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17, ReportLab |
| Web   | Vue 3, Vite, TypeScript, Vue Router                                    |
| Tests | pytest (against a real Postgres), Vitest + Vue Test Utils              |
| Run   | Docker Compose: postgres, api (uvicorn), web (nginx)                   |

## Quick start with Docker

```bash
docker compose up --build
```

Open http://localhost:4412 and sign in with the demo account:

- **Email:** `demo@example.com`
- **Password:** `demo-password`

The demo user is created on first start with:

- three clients in GBP and EUR (one with a project rate override) plus an
  internal, non-billable "Admin" project;
- about six months of weekday time entries from the timer, forms and grid,
  rounded to 6 minutes when invoiced;
- monthly invoices for every client: older ones paid, last month's sent (and
  overdue once the 14 day terms pass), a draft for the current month with a
  PO reference, and 20% VAT on the GBP client;
- a 100 hour budget on "Booking app" that is close to running out, and a
  30 hour weekly target.

Set `SEED_DEMO=false` to start with an empty database. Data lives in the
`db-data` volume; `docker compose down -v` removes it. Outside Docker, run
`python -m timesheets.seed` (`--days 365` for a longer history).

```bash
WEB_PORT=8080 docker compose up -d      # another port
docker compose logs -f api              # API logs (one line per request)
```

## Local development

You need Python 3.12, Node 22 and a PostgreSQL database. The easiest database
is the one from the compose file: `docker compose up -d db` and expose it with a
`ports: ['5432:5432']` override, or use your own.

```bash
# API on :8000
cd api
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # point DATABASE_URL at your database
alembic upgrade head
python -m timesheets.seed     # optional demo data
uvicorn timesheets.main:app --reload

# Web app on :5173, proxies /api to :8000 (override with API_URL)
cd web
npm install
npm run dev
```

FastAPI's interactive docs are at http://localhost:8000/docs.

## Configuration

API settings come from environment variables (or `api/.env`):

| Variable            | Default                                   | Description                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------- |
| `DATABASE_URL`      | `postgresql+psycopg://...@localhost/...`  | SQLAlchemy URL of the database              |
| `SECRET_KEY`        | development value                         | signs access tokens; set a long random one  |
| `TOKEN_TTL_MINUTES` | `10080` (7 days)                          | access token lifetime                       |
| `CORS_ORIGINS`      | `http://localhost:5173`                   | comma separated browser origins             |
| `LOG_LEVEL`         | `info`                                    | `debug`, `info`, `warning`...               |
| `LOG_FORMAT`        | `text`                                    | `json` for one JSON object per line         |
| `SEED_DEMO`         | `false` (`true` in docker compose)        | create the demo account on container start  |

Compose variables: `WEB_PORT` (default `4412`), `SECRET_KEY`, `SEED_DEMO`,
`LOG_LEVEL`.

## Tests

```bash
# API: needs an empty Postgres database it may drop and recreate the schema of
cd api
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/timesheets_test pytest
ruff check . && ruff format --check .

# Web
cd web
npm test            # vitest, runs in the Pacific/Auckland time zone on purpose
npm run lint && npm run format:check && npm run typecheck
npm run build
```

The API tests build the schema by running the Alembic migrations and check
that the migrated schema matches the models. CI (`.github/workflows/ci.yml`)
runs all of the above and builds the Docker images.

## Project layout

```
api/
  timesheets/
    main.py         app factory, middleware, routers
    models.py       SQLAlchemy models
    routers/        HTTP endpoints, one module per area
    schemas/        Pydantic request and response models
    services/       rounding, money, timesheet, invoicing, reports, pdf
    seed.py         demo data (python -m timesheets.seed)
  migrations/       Alembic migrations
  tests/
web/
  src/
    api/            fetch client and response types
    components/     timer bar, forms, grid cell, charts...
    views/          one per page
    stores/         auth, timer, projects, toasts
    lib/            formatting, week and grouping helpers
docs/
  api.md            API reference
  architecture.md   how the pieces fit together
```

## Contributing

- Branch from `main` and keep commits small; messages follow
  [Conventional Commits](https://www.conventionalcommits.org/) (`feat(api): ...`,
  `fix(web): ...`).
- Schema changes need a migration: change `models.py`, then
  `alembic revision --autogenerate -m "what changed"`, read the generated file
  (autogenerate misses partial indexes and server defaults now and then) and
  run `alembic upgrade head`. The test suite fails when models and migrations
  drift apart.
- Bug fixes come with a regression test. `make lint test` before pushing runs
  what CI runs.

## License

MIT, see [LICENSE](LICENSE).
