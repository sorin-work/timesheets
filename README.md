# timesheets

Time tracking and invoicing for freelancers.

- **Clients and projects** with hourly rates; a project can override its client's rate
- **Running timer** in the top bar, plus manual entries
- **Weekly timesheet** where you can type hours straight into the grid
- **Rounding rules**: none, 6 minutes or 15 minutes, applied per entry when invoicing
- **Invoices** generated from unbilled time, with tax lines and a PDF download
- **Reports** of tracked time by client, project or month, and revenue per month

## Quick start with Docker

```bash
docker compose up --build
```

Open http://localhost:4412 and sign in with the demo account:

- **Email:** `demo@example.com`
- **Password:** `demo-password`

The demo user is created on first start with six months of time entries and
invoices. Set `SEED_DEMO=false` to start with an empty database.

## Local development

You need Python 3.12, Node 22 and PostgreSQL.

```bash
# API on :8000
cd api
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # point DATABASE_URL at your database
alembic upgrade head
python -m timesheets.seed     # optional demo data
uvicorn timesheets.main:app --reload

# Web app on :5173 (proxies /api to :8000)
cd web
npm install
npm run dev
```

## Tests

```bash
cd api && pytest      # needs a Postgres database, see TEST_DATABASE_URL
cd web && npm test
```

## License

MIT
