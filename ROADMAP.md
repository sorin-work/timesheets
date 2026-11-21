# Roadmap

Things I might add to timesheets. The app covers the loop a freelancer needs
today (track, fill in the week, invoice, get paid, report), so nothing here is
promised or scheduled. These are ideas, written down with enough detail that I
(or anyone else) can pick one up later without starting from zero. Items may
change, move between groups or be dropped.

What the app does today is in the [README](README.md) and the notes under
[docs/](docs/).

- **Next**: small or well understood, mostly gaps in what already exists. I
  would start with these.
- **Later**: worth doing, but bigger or waiting on a decision.
- **Maybe**: not sure yet that they are worth the extra complexity.

Sizes are rough: **S** is an evening or two, **M** a few evenings up to a
couple of weekends, **L** several weeks of spare time.

Each item is meant to fit in one pull request and to be covered by the test
suite. There are no browser tests: `api/tests` runs pytest against a real
PostgreSQL (the schema is built by running the migrations), and the web app has
Vitest specs in `__tests__` folders next to the code, run in the
Pacific/Auckland time zone on purpose. So rules worth testing (rounding, money,
periods, numbering) belong in `services/`, which is unit tested on its own, and
not inside a router or a component; pure web helpers belong in `web/src/lib`.
Most items add columns or tables and bring their own Alembic migration under
`api/migrations/versions`, and the suite fails when models and migrations drift
apart. File names below are relative to `api/timesheets/` unless they start
with `api/`, `web/` or `docs/`.

When an item ships, its row in the overview says `Shipped` in the Group column,
its section moves under a `## Shipped` heading at the end of this file and
shrinks to one paragraph on what was built and what was left out, and the same
pull request updates the README, the notes under `docs/` and an `Unreleased`
entry in the [CHANGELOG](CHANGELOG.md).

"Depends on" lists real prerequisites only. Items that merely touch the same
file are not listed there; the bigger overlaps are mentioned in the items.

## Overview

| #   | Item                                          | Group | Area        | Size | Depends on |
| --- | --------------------------------------------- | ----- | ----------- | ---- | ---------- |
| 1   | One time zone for periods, reports and CSV    | Next  | correctness | M    | -          |
| 2   | Invoices keep the details they were sent with | Next  | invoices    | S    | -          |
| 3   | Deleting a project with invoiced time         | Next  | correctness | S    | -          |
| 4   | Sign-in limit per person, not per proxy       | Next  | security    | S    | -          |
| 5   | Scheduled backups and a restore guide         | Next  | ops         | S    | -          |
| 6   | Overlapping entries                           | Later | entries     | S    | -          |
| 7   | Editing time lines on a draft invoice         | Later | invoices    | M    | -          |
| 8   | Partial payments                              | Later | invoices    | M    | -          |
| 9   | Credit notes instead of reverting             | Later | invoices    | M    | -          |
| 10  | Invoice numbers taken when sent               | Later | invoices    | S    | -          |
| 11  | Rates that change on a date                   | Later | billing     | M    | -          |
| 12  | Rounding per client and rounding modes        | Later | billing     | S    | -          |
| 13  | Tags on entries                               | Later | entries     | M    | -          |
| 14  | Budgets in money and per month                | Later | projects    | M    | -          |
| 15  | Fixed-fee projects and milestones             | Later | billing     | M    | -          |
| 16  | Expenses with receipts                        | Later | billing     | M    | -          |
| 17  | Recurring invoices                            | Later | invoices    | M    | -          |
| 18  | Optional email: sending invoices              | Later | invoices    | M    | -          |
| 19  | Payment reminders                             | Later | invoices    | S    | 18         |
| 20  | Password reset                                | Later | accounts    | S    | 18         |
| 21  | Sessions that can be revoked                  | Later | security    | M    | -          |
| 22  | Short-lived PDF links                         | Later | security    | S    | -          |
| 23  | Two-factor sign-in                            | Later | security    | M    | -          |
| 24  | Import from other trackers                    | Later | import      | M    | -          |
| 25  | Full account export                           | Later | accounts    | M    | -          |
| 26  | Locked periods                                | Later | entries     | S    | -          |
| 27  | Week start, date and number formats           | Later | ui          | S    | -          |
| 28  | Invoice PDF: logo, language and layout        | Later | invoices    | M    | 2          |
| 29  | Accessibility pass                            | Later | ui          | M    | -          |
| 30  | Browser end-to-end tests                      | Later | tests       | M    | -          |
| 31  | Metrics and a readiness check                 | Later | ops         | S    | -          |
| 32  | Idle and forgotten-timer reminders            | Maybe | timer       | S    | -          |
| 33  | Calendar day view                             | Maybe | entries     | L    | -          |
| 34  | Personal API tokens                           | Maybe | api         | M    | 21         |
| 35  | Faster with years of data                     | Maybe | performance | M    | -          |
| 36  | Totals across currencies                      | Maybe | reports     | M    | -          |
| 37  | Read-only invoice links for clients           | Maybe | invoices    | M    | 2          |
| 38  | Installable app with an offline timer         | Maybe | timer       | L    | -          |

## Next

### 1. One time zone for periods, reports and CSV

The weekly grid works in the time zone from Settings (`services/timesheet.py`
builds days with `ZoneInfo(user.timezone)`), but almost everything else still
cuts days at UTC midnight:

- `unbilled_entries` in `services/invoicing.py` turns `period_start` and
  `period_end` into UTC bounds. For someone in Auckland, an entry started at
  08:00 on the 1st local time is 19:00 on the 31st in UTC and lands on the
  previous month's invoice. The invoice preview (`/api/invoices/unbilled`)
  uses the same function, so the preview and the invoice agree with each
  other but not with the grid.
- `_day_start` in `routers/entries.py` does the same for the `from` and `to`
  filters, so the entries page and its CSV disagree with the timesheet near
  midnight.
- `time_report` in `services/reports.py` uses UTC bounds, and its `month`
  grouping formats `started_at.astimezone(UTC)`. `revenue_report` puts a
  payment in the UTC month of `paid_at`.
- The dashboard's "today" and "this week" in `routers/dashboard.py` start at
  UTC midnight of `clock.today()`, which is itself the UTC date.
- The CSV export writes `started_at.strftime("%H:%M")` on a UTC value, so the
  start and end columns are UTC times without saying so.

What to build:

- A small `services/periods.py` with `local_day_bounds(day, tz)` and
  `local_range(date_from, date_to, tz)` that return aware UTC datetimes, and
  `local_today(user)`. The grid's `_local_midnight` moves there too.
- Every place above uses it. The month grouping converts to the user's zone
  before formatting. The CSV converts both times and adds a header comment or
  a `timezone` column; I lean towards the column, because spreadsheet imports
  drop comments.
- `pay_invoice` stores `paid_on` as noon UTC. Keep that, but compare it as a
  local date in the revenue report.
- Tricky: invoices already generated keep their entries. Changing the bounds
  only affects new invoices, and an entry that moves to another period was
  either already billed or still unbilled; nothing gets billed twice, because
  the `invoice_id IS NULL` filter stays.
- Tricky: daylight saving. A local day is 23 or 25 hours twice a year. Build
  bounds by combining the date with midnight in the zone (as the grid does),
  never by adding 24 hours.
- Tricky: `clock.today()` is the single pinned clock in tests. Add
  `clock.today_in(tz)` rather than a second source of time.
- Tests: `api/tests/test_periods.py` for the helpers across a DST change;
  regressions in `test_invoicing.py`, `test_entries.py`, `test_reports.py`
  and `test_dashboard.py` with a user in `Pacific/Auckland` and an entry just
  after local midnight.

### 2. Invoices keep the details they were sent with

An invoice stores its lines, taxes and currency, but not who it is from or to.
`render_invoice_pdf` in `services/pdf.py` reads `invoice.client.name`,
`invoice.client.address`, `user.business_name`, `user.business_address`,
`user.tax_id` and `user.payment_details` at download time. Moving house,
changing bank, or fixing a typo in a client's address therefore rewrites every
invoice already sent and paid, which is exactly what an invoice must not do.

- Data: on `Invoice`, `seller_name`, `seller_address`, `seller_tax_id`,
  `payment_details`, `client_name`, `client_address` (all nullable text). A
  migration fills them for existing rows from the current user and client,
  which is the best that can be done for old invoices.
- `generate_invoice` copies them in. While the invoice is a draft, the
  `PATCH /api/invoices/{id}` route refreshes them from the current settings on
  every save, so a draft follows the settings; `change_status(..., "send")`
  takes a last copy and from then on they are frozen.
- `render_invoice_pdf` and the invoice view read the stored values only.
  `InvoiceDetail` gains the fields; `client_name` becomes a column instead of
  the relationship property.
- Tricky: `revert` takes a sent invoice back to draft. After that the
  snapshot refreshes again, which is right if it was never really sent. Item 9
  replaces most reverts with credit notes anyway.
- Undecided: whether to show "details changed since this invoice was sent" on
  the invoice page. Cheap and useful; I would add it.
- Tests: in `test_invoices.py`, change the client address and business
  details after sending and check the PDF text (ReportLab output can be read
  back with `pypdf`, or the test can check the values passed to the renderer)
  and the detail response still carry the old ones; a draft follows the
  change.

### 3. Deleting a project with invoiced time

`delete_project` in `routers/projects.py` deletes the row, and
`TimeEntry.project_id` is `ondelete="CASCADE"`. If the project has time on a
sent or paid invoice, those entries disappear. The invoice keeps its lines
(their `project_id` goes to `NULL`), so the totals stay, but
`Invoice.entry_count` drops, the entries can no longer be listed or exported,
and the client summary's tracked hours shrink. Clients already refuse deletion
when they have invoices (`delete_client` answers 409 with "archive it
instead"); projects should do the same.

- Refuse with `Conflict` when any entry of the project has an `invoice_id`.
  Suggest archiving, as the client route does.
- Also refuse while a timer runs on the project, for the same reason
  `archive_project` stops it.
- Change the foreign key to `RESTRICT` for invoiced entries? Postgres cannot
  restrict conditionally, so keep `CASCADE` and enforce it in the route; the
  invariant goes into `docs/architecture.md` next to "An entry with
  `invoice_id` set is locked".
- The projects page shows a delete button only for projects without invoiced
  time; `ProjectOut` gains `has_invoiced_time`.
- Same check for deleting a client: `delete_client` checks invoices, which
  covers invoiced entries, but say so in a comment.
- Tests: `test_projects.py`: delete refused with invoiced entries, allowed
  with only unbilled ones, and the unbilled ones go with it.

### 4. Sign-in limit per person, not per proxy

`limit_auth` in `ratelimit.py` keys attempts on `request.client.host`. In the
compose setup every request comes through nginx in the `web` container.
Uvicorn runs with `--proxy-headers`, but it only trusts `X-Forwarded-For` from
`127.0.0.1` by default, and nginx is another container. So the key is nginx's
address for everyone: ten failed sign-ins by anybody in five minutes lock out
every user of the instance, and one person guessing passwords is limited no
more than a crowd.

- Configuration: `FORWARDED_ALLOW_IPS` (passed to uvicorn as
  `--forwarded-allow-ips`), set in `docker-compose.yml` to the compose
  network, and documented in the README table. Outside Docker it stays at the
  safe default.
- Key the login limit on the email as well as the address: at most N failures
  per email per window, independent of the address, so a spread-out guess at
  one account is still slowed. Count failures only, so a person who signs in
  fine is not limited.
- Tricky: the limiter is in memory per process and the module says so. Keep
  it that way; the compose stack runs one process. Note it in the
  troubleshooting doc.
- Tricky: an attacker can lock someone out by failing on their email. Keep
  the per-email window short (15 minutes) and the message generic, as today.
- Tests: `test_ratelimit.py` with two client addresses (the test client can
  set them) and with one address and two emails.

### 5. Scheduled backups and a restore guide

The data is a freelancer's income record, and it lives in one Docker volume
(`db-data`). There is no backup, and the README only says that
`docker compose down -v` removes it.

- A `backup` service in `docker-compose.yml` under a `backup` profile, using
  the same `postgres:17-alpine` image: a loop that runs `pg_dump -Fc` once a
  day into a `./backups` bind mount, named by date, and deletes dumps older
  than `BACKUP_KEEP_DAYS` (default 30). No hosted storage; copying the folder
  elsewhere is the user's job, and the doc says so.
- `docs/backups.md`: how to start it, how to take one by hand
  (`docker compose exec db pg_dump ...`), how to restore into a fresh volume,
  and how to check a dump with `pg_restore --list`.
- Upgrades: the API runs `alembic upgrade head` on start
  (`docker-entrypoint.sh`). The doc should say to take a dump before pulling a
  new version, because there are no down migrations in practice.
- Tricky: restoring needs the API stopped, or the entrypoint migrates a
  half-restored database. The guide stops `api` first.
- Undecided: a "Download backup" button in Settings. That would be a per-user
  export, which is item 25, not a database backup.
- Tests: none in pytest. A CI step that runs the backup script once against
  the service database and restores it into a second database would prove the
  commands; it fits in the existing `api` job.
