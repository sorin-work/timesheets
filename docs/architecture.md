# Architecture notes

```
browser ──> nginx (web container, :80)
              ├── /          static Vue build, SPA fallback to index.html
              └── /api/ ───> uvicorn + FastAPI (api container, :8000) ───> PostgreSQL
```

## API (`api/`)

- `timesheets/main.py` builds the app: CORS, request id + access log
  middleware, JSON error handlers and the routers.
- `routers/` are thin HTTP layers: parse input with the Pydantic schemas in
  `schemas/`, load rows through `routers/common.get_owned` (which returns 404
  for rows of other users, so ids never leak), call a service, return a schema.
- `services/` hold the domain rules and are unit tested on their own:
  - `rounding.py`: billing increments, always rounding *up* per entry;
  - `money.py`: Decimal helpers, half-up rounding to cents;
  - `timesheet.py`: the weekly grid in the user's time zone and cell edits;
  - `invoicing.py`: unbilled time, invoice numbers, generation, totals, status;
  - `reports.py`, `pdf.py`.
- `models.py` is the whole schema (SQLAlchemy 2 typed mappings). Alembic
  migrations live in `migrations/versions` and are written with
  `alembic revision --autogenerate`, then reviewed. The test suite builds its
  schema by running the migrations and checks they match the models.
- `clock.py` is the only place that asks for "today", so tests can pin it.

### Invariants worth knowing

- Durations are computed from `started_at`/`ended_at`; there is no stored
  duration column. A running timer has `ended_at IS NULL`, and a partial unique
  index allows only one per user.
- An entry with `invoice_id` set is locked. Deleting a *draft* invoice releases
  its entries; sent and paid invoices cannot be deleted.
- Invoice generation locks the entries it bills (`SELECT ... FOR UPDATE`), so two
  parallel requests cannot bill the same time.
- `overdue` is not stored: it is a sent invoice whose due date is in the past.
- Money never goes through floats. Line amount = hours (2 decimals) x rate,
  rounded half up; taxes are computed on the subtotal.

## Web (`web/`)

- Vue 3 with `<script setup>` and TypeScript, Vue Router, no state library:
  small reactive stores in `src/stores` (auth, timer, projects, toasts).
- `src/api/client.ts` wraps `fetch`, adds the bearer token, turns error bodies
  into `ApiError` (with field errors for forms) and sends you to the login page
  on a 401.
- Views live in `src/views`, reusable pieces in `src/components`, pure helpers
  in `src/lib` (formatting, week maths, grouping). Tests sit next to them in
  `__tests__` folders and run in the Pacific/Auckland time zone on purpose.
