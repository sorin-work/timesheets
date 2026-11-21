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

## Later

### 6. Overlapping entries

Nothing stops two entries from covering the same minutes. A manual entry typed
over a stretch the timer already recorded, or a grid cell on a day with timer
entries at 09:00 (`set_cell` always starts its entry at 09:00 local), bills
the same hour twice. Toggl and Clockify both flag this; for invoicing it
matters more than for plain tracking.

- A pure `find_overlaps(entries)` in a new `services/overlaps.py` that returns
  pairs of entry ids whose ranges intersect, ignoring touching ends.
- `create_entry` and `update_entry` in `routers/entries.py` look up the
  user's entries that intersect the new range (one query on
  `ix_time_entries_user_started`) and answer with the entry plus a
  `warnings` list. Not a refusal: people do work on two things at once now and
  then, and the warning is enough.
- The entries page marks overlapping rows and the timesheet shows a dot on
  days that have them. The invoice preview counts overlapping minutes so they
  can be fixed before billing.
- Grid entries: they have no real start time, so they never count as
  overlapping. Their time is a total, not a range.
- Tricky: the running timer overlaps anything that starts after it. Treat its
  end as now, the way `duration_seconds` does.
- Tests: unit tests for `find_overlaps`; route tests for the warning on
  create and update and none for grid entries.

### 7. Editing time lines on a draft invoice

A draft can get extra lines, taxes, notes and dates, but the lines built from
tracked time are fixed: `remove_extra_line` refuses them ("delete the draft
instead") and there is no route to change their text or hours. Rewording
"Booking app" to "Booking app: payment flow", writing off half an hour, or
merging two per-entry lines means deleting the draft, editing entries and
generating again.

- `PATCH /api/invoices/{id}/lines/{line_id}` on drafts: `description`, and
  for time lines a `quantity` override. Extra lines may change everything.
- Data: `tracked_quantity Numeric(10, 2)` on `InvoiceLine`, filled at
  generation, so the invoice page can show "billed 7.50 h of 8.20 h tracked"
  and a reset button.
- `recalculate` stays the single source of totals.
- Tricky: the entries stay linked to the invoice whatever the quantity says.
  A written-off half hour is still "invoiced", which is the honest state (it
  was dealt with) and keeps it out of the next invoice.
- Tricky: regenerating. A "Refresh from time" action on a draft would rebuild
  the time lines and drop the edits. Leave it out; deleting the draft does the
  same thing visibly.
- Tests: in `test_invoices.py`, edit text and hours, totals follow, refused on
  sent invoices, reset restores `tracked_quantity`.

### 8. Partial payments

`change_status(..., "pay")` marks the whole invoice paid at one date, and
`unpay` clears it. Clients pay in parts, short-pay because of bank fees, or
pay two invoices with one transfer. The revenue report then shows the full
total in the month of the last part.

- Data: an `InvoicePayment` table: `invoice_id`, `amount`, `paid_on`, `note`.
  `Invoice.paid_at` stays as "fully paid at" and is set when the payments
  reach the total.
- `POST /api/invoices/{id}/payments` and `DELETE .../payments/{payment_id}`.
  The existing `pay` action becomes "record a payment of the remaining
  balance", so the one-click flow stays.
- `InvoiceDetail` gains `paid_amount` and `balance`. The list and overview
  show "part paid" as a display status next to `overdue`; like `overdue`, it is
  derived, never stored.
- `revenue_report` sums payments by `paid_on` instead of invoice totals by
  `paid_at`. The client summary's `paid` and `outstanding` follow.
- Tricky: overpayment. Refuse a payment above the balance; a client credit
  balance is out of scope.
- Tricky: the migration creates one payment per paid invoice from `total` and
  `paid_at`, so old reports do not change.
- Undecided: a write-off action that closes an invoice with a balance left
  (bank fees). I lean towards a payment with a note, which needs nothing new.
- Tests: `test_invoicing.py` for the balance and status rules,
  `test_reports.py` for revenue by payment month.

### 9. Credit notes instead of reverting

The only way to correct a sent invoice is `revert`, which puts it back to
draft so it can be edited or deleted. In most countries an issued invoice may
not be changed or removed; it is cancelled with a credit note that references
it. Reverting also releases nothing, but deleting the reverted draft releases
its entries and leaves a gap in the numbers.

- Data: `kind` on `Invoice` (`invoice` or `credit_note`) and
  `credits_invoice_id`. A credit note has its own number series
  (`credit_prefix` in settings, default `CN-`) and negative lines.
- `POST /api/invoices/{id}/credit` on a sent or paid invoice creates a credit
  note for all of it, sent immediately. The original gets display status
  `credited`. Its entries are released only if the user ticks "bill this time
  again", which covers the usual case of re-invoicing with a fix.
- `revert` is kept only for invoices that were marked sent by mistake and
  never left the app: allowed within, say, 24 hours of `sent_at`, and only
  when no PDF was downloaded since (a `downloaded_at` column set by
  `invoice_pdf`).
- Reports: credit notes count as negative revenue in the month they are
  issued.
- Tricky: partial credit (one line wrong) means editing lines on the credit
  note, which reuses item 7's line editing if it exists.
- Tests: the new transitions in `test_invoicing.py`, numbering, released
  entries, revenue in `test_reports.py`.

### 10. Invoice numbers taken when sent

`generate_invoice` gives a draft its number at once (`next_number` takes
`max(sequence) + 1`). Deleting a draft that is not the newest leaves a gap, and
deleting the newest one hands its number to the next draft. Drafts that sit
for a week can also end up numbered out of date order with invoices sent in
between. Many tax offices expect gapless numbers in issue order.

- Drafts get no number: `number` and `sequence` become nullable, and the list
  shows "Draft" in the number column. The unique constraint
  `uq_invoices_user_number` already ignores nulls.
- `change_status(..., "send")` takes the next number inside the transaction,
  with a `SELECT ... FOR UPDATE` on the user's row so two sends cannot race.
  The `IntegrityError` retry message in `generate_invoice` moves there.
- `revert` keeps the number, so the series stays without gaps; a reverted
  invoice is sent again with the same number.
- The PDF of a draft says "Draft" instead of a number. Sorting by number puts
  drafts first or last explicitly.
- Tricky: existing drafts keep their numbers in the migration (taking them
  away would surprise anyone who already shared one); only new drafts are
  unnumbered.
- Undecided: whether to offer both behaviours as a setting. I would not; one
  rule is easier to explain.
- Tests: numbering in `test_invoicing.py` with deleted drafts, two parallel
  sends (two sessions, as the existing double-generate test does), revert and
  send again.

### 11. Rates that change on a date

The rate is read when the invoice is generated: `_rate` uses
`project.effective_rate`, and reports and the dashboard value unbilled time the
same way. Raising a client's rate on 1 January also raises December's
unbilled hours. The usual answer is "invoice before you change the rate",
which is easy to forget.

- Data: a `Rate` table: `client_id` or `project_id`, `hourly_rate`,
  `valid_from` (a date). The current `hourly_rate` columns become "the rate
  without a date" and a migration turns them into rows from the beginning of
  time.
- A pure `rate_on(project, day)` in `services/rates.py`: the project's latest
  rate on or before the day, else the client's. `_build_lines` groups by
  project and rate, so a period that spans a change produces two lines
  ("Booking app, until 31 Dec" and "from 1 Jan").
- The entry's day is the local day from item 1.
- Forms: "change rate from date" on the client and project pages, with the
  history listed.
- Tricky: `TimeEntry.hourly_rate` and `ProjectOut.effective_rate` are used by
  the web app for value columns. They become "rate for this entry" and "rate
  today".
- Tests: `test_rates.py` for `rate_on`; invoice generation across a change.

### 12. Rounding per client and rounding modes

Rounding is one setting for the whole account (`User.rounding`: none, 6 or 15
minutes) and always rounds each entry up. Agencies often agree a rule per
client, and some clients only accept rounding of the daily or invoice total,
or to the nearest step.

- Data: `rounding` and `rounding_mode` on `Client`, nullable (null follows the
  account setting). Modes: `entry_up` (today), `entry_nearest`, `total_up`
  (round each invoice line's sum once).
- `round_seconds` gains a `mode`; `_build_lines` passes the client's rule. In
  `group_by == "entry"` the total modes behave like `entry_*`, and the form
  says so.
- The preview, dashboard and reports all call `round_seconds` today with
  `user.rounding`. A helper `rule_for(client, user)` keeps them consistent.
- Tricky: nearest can round a 2 minute entry to zero. Keep it, with a note in
  the troubleshooting doc, or set a minimum of one step. I lean towards the
  minimum.
- Tests: `test_rounding.py` for the modes, one generation test per mode.

### 13. Tags on entries

Entries have a project and a free-text description. There is no way to say
"meeting", "bug fix" or "travel" and then report on it. Every comparable tool
has tags, and they are the most common request on the tracker forums.

- Data: `Tag` (`user_id`, `name`, unique per user) and `entry_tags`. Tags are
  created by typing a new one.
- API: `tag_ids` on `EntryIn`, `EntryUpdate` and `TimerStart`; a `tag` filter
  in `EntryFilters`; bulk add and remove in `/api/entries/bulk`.
- Web: a tag picker in `EntryForm.vue` and `TimerBar.vue`, tags as chips in the
  entries list, a tag filter kept in the URL like the others.
- Reports: group by tag in `time_report`. An entry with two tags counts in
  both rows, and the total row says the rows overlap.
- The CSV export gets a `tags` column.
- `continue_entry` copies the tags.
- Tests: route tests for create, filter and bulk; report grouping.

### 14. Budgets in money and per month

A project can have `budget_hours`, counted over its whole life, and the
dashboard warns at 80% (`BUDGET_WARNING_PERCENT`). Retainers ("20 hours a
month") and fixed budgets ("up to 5,000 EUR") cannot be expressed.

- Data: on `Project`, `budget_kind` (`hours` or `money`), `budget_amount`,
  `budget_period` (`total` or `month`). `budget_hours` is migrated into it.
- `with_usage` in `routers/projects.py` computes usage for the current period
  (the local month from item 1 for monthly budgets) and in money when needed,
  with the same rounding as invoicing.
- `BudgetBar.vue` shows hours or money and "this month".
- Optional: a notice when starting the timer on a project that is over
  budget.
- Tricky: money budgets need a rate for every entry; time on a project without
  a rate is shown as unknown, not zero.
- Tests: usage calculation in a service test, dashboard warning for a monthly
  budget that resets.

### 15. Fixed-fee projects and milestones

Every project is billed by the hour. Plenty of freelance work is quoted at a
fixed price, often in parts ("40% upfront, 60% on delivery"), while the time
is still tracked to see whether the quote was right.

- Data: `billing` on `Project` (`hourly` or `fixed`) and a `Milestone` table
  (`project_id`, `name`, `amount`, `invoice_id`, `due_on`).
- Time on a fixed project is never billed as hours: `unbilled_entries` skips
  it, and the preview says why.
- Invoicing: the new-invoice page lists unbilled milestones next to unbilled
  hours, and generating puts them on as lines with `project_id` set and
  quantity 1.
- Project page: quoted amount, invoiced so far, hours tracked and the
  effective hourly rate.
- Tricky: switching a project from hourly to fixed with unbilled time. Ask
  whether that time is billed separately or covered by the fee.
- Tests: generation with milestones, hourly time skipped, effective rate.

### 16. Expenses with receipts

Expenses go on an invoice only as hand-typed extra lines on a draft
(`add_extra_line`). There is no record of an expense before the invoice
exists, no receipt, and nothing reminds anyone to bill it.

- Data: `Expense` (`user_id`, `project_id`, `spent_on`, `description`,
  `amount`, `currency`, `billable`, `invoice_id`, `receipt_path`).
- Receipts stored on a volume (`/data/receipts`, a new compose volume), with a
  size cap and a type check by content (PDF, JPEG, PNG). Served through an
  owned route like the invoice PDF.
- Invoice generation picks up unbilled billable expenses of the client in the
  period as extra lines, linked like entries are, and deleting a draft
  releases them.
- Expenses in another currency than the client's are refused for invoicing
  until converted by hand; see item 36.
- Tricky: backups. Item 5 has to include the receipts volume, or a restore
  loses them.
- Tests: upload limits, ownership of receipt downloads, generation and
  release.

### 17. Recurring invoices

Fixed monthly fees (hosting, maintenance, retainers) mean typing the same
draft every month.

- Data: `RecurringInvoice` (`client_id`, lines and taxes as JSON, `interval`
  monthly or quarterly, `next_issue_on`, `active`).
- Nothing runs in the background today. Rather than adding a scheduler, the
  API creates due drafts lazily: the dashboard and invoices list call
  `materialise_due(user)` first, which creates every draft whose
  `next_issue_on` has passed, in a transaction, and moves the date on.
- Drafts only. Sending stays a person's decision.
- Tricky: catching up. After three months away, create three drafts dated
  correctly, not one.
- Tricky: two tabs loading the list at once. Lock the recurring row with
  `FOR UPDATE` while materialising.
- Tests: due drafts created once, catch-up, inactive ones skipped.

### 18. Optional email: sending invoices

"Mark as sent" only changes a status; the PDF goes out through the user's own
mail program. `Client.email` exists but is used for nothing except search.

- Optional SMTP settings in the environment (`SMTP_HOST`, `SMTP_PORT`,
  `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`). Without them, the feature is
  hidden and nothing changes. The compose file gets a mailpit service under a
  `mail` profile for local testing.
- "Send by email" on a draft: a dialog with recipient (client email), subject
  and body from a template in settings, the PDF attached. On success it calls
  the same `change_status(..., "send")`.
- Data: an `InvoiceEmail` log (`invoice_id`, `to`, `sent_at`, `error`) shown on
  the invoice page.
- Sending happens in the request, with a timeout; a failure leaves the invoice
  a draft and shows the SMTP error.
- Tricky: reply-to. Mail from the server's address with the user's email as
  `Reply-To`, so replies reach the person.
- Tests: an SMTP stub (`aiosmtpd` or a fake transport injected in tests) for
  the message content and attachment, failure leaves a draft.

### 19. Payment reminders

Overdue invoices are shown as `overdue` and counted on the dashboard, and
that is all. Chasing payment is the part freelancers dislike most.

- "Send reminder" on an overdue invoice, using item 18's mail with a reminder
  template and the PDF attached again. Logged in the same `InvoiceEmail`
  table, so the invoice page shows when the client was last reminded.
- Optional automatic reminders: N days after the due date, at most M times.
  Without a scheduler, the same lazy approach as item 17 sends due reminders
  when the user opens the app. That is a real limit (no reminders while the
  app is closed), and the settings page has to say so.
- Tricky: never remind for an invoice that was paid meanwhile; check the
  status inside the send.
- Depends on item 18.
- Tests: due reminders chosen correctly, none for paid invoices, limit
  respected.

### 20. Password reset

There is no way back into an account after forgetting the password. Signup
and login exist, and `change_password` needs the current one.

- With item 18's SMTP configured: "Forgot password" sends a link with a
  random token. Data: `PasswordReset` (`user_id`, `token_hash`, `expires_at`,
  `used_at`). Tokens are stored hashed, expire after an hour and work once.
- Without SMTP: a `python -m timesheets.reset_password <email>` command for
  the person running the server, documented in troubleshooting.
- The request answers the same whether the email exists or not, and goes
  through `limit_auth`.
- Resetting invalidates existing sessions once item 21 exists.
- Tests: token single use and expiry, same response for unknown emails, rate
  limit applied.

### 21. Sessions that can be revoked

Access tokens are seven-day JWTs (`TOKEN_TTL_MINUTES` default 10080) with no
server-side record. Changing the password does not sign anyone out, deleting a
lost laptop's session is impossible, and signing out only removes the token
from `localStorage`.

- Data: `Session` (`user_id`, `id`, `created_at`, `last_seen_at`,
  `user_agent`, `revoked_at`). The JWT carries the session id as `sid`, and
  `_user_for_token` in `deps.py` checks the row.
- `change_password` revokes every other session. Settings gets a list of
  sessions with "sign out" and "sign out everywhere else". Logout revokes the
  current one on the server.
- `last_seen_at` is updated at most once a minute per session, so not every
  request writes.
- Tricky: this adds a query per request. It is one primary key lookup; worth
  it.
- Undecided: moving the token from `localStorage` to an HttpOnly cookie. It
  protects against token theft through XSS but needs CSRF protection. Vue
  escapes output and notes are already rendered as text, so I would keep the
  bearer token and revisit with item 34.
- Tests: revoked session gets 401, password change revokes others, listing
  shows only own sessions.

### 22. Short-lived PDF links

The PDF link on the invoice page is `/api/invoices/{id}/pdf?token=...` with
the full access token (`get_download_user` in `deps.py`). That token is valid
for a week and grants everything. It ends up in browser history and in
nginx's access log, which logs the query string (the API's own log line only
logs the path).

- `POST /api/invoices/{id}/download` returns a link with a signed token that
  is good for one invoice, one minute and the PDF route only (a JWT with
  `scope=invoice-pdf` and `invoice_id`). The view requests it on click, then
  opens the link.
- `get_download_user` stops accepting access tokens in the query string.
- Same mechanism for the CSV exports, which today are fetched with the bearer
  header and turned into a blob; they can stay that way.
- Tests: scoped token works once for its invoice, refused for another invoice
  and after expiry, a normal access token in `?token=` is refused.

### 23. Two-factor sign-in

The account holds bank details (`payment_details`), client addresses and the
income history. A second factor is a reasonable option for people who host
this on the internet.

- TOTP with `pyotp`: enable in settings with a QR code (rendered in the
  browser from the `otpauth://` URI, no service), confirm with a code, show ten
  recovery codes once (stored hashed).
- Login becomes two steps when enabled: the password step returns a
  short-lived `mfa_token`, and `POST /api/auth/login/totp` exchanges it plus a
  code for the access token. Both steps go through `limit_auth`.
- Disabling needs the password and a code.
- Tricky: clock drift. Accept one step either side.
- Tests: enable, login with and without code, recovery code used once,
  disable.

### 24. Import from other trackers

Moving from Toggl, Clockify or Harvest means starting with an empty history,
or typing it in. All three export CSV.

- `POST /api/import/entries` with a CSV file and a `format`
  (`toggl`, `clockify`, `harvest`, or `timesheets`, the app's own export
  format). A dry run returns what would be created: new clients and projects
  matched by name, entry count, rows that fail and why.
- A pure parser per format in `services/importers.py` that yields
  `(client, project, start, end, description, billable)` and has unit tests
  with sample files in `api/tests/fixtures`.
- Imported entries get `source="import"`, and all of them come from one
  request in one transaction, with a batch id so a bad import can be undone
  in one action.
- Tricky: time zones. Toggl exports local times without an offset; the import
  form asks for the zone and defaults to the account's.
- Tricky: size. Cap the file (5 MB) and the rows (50,000).
- Tests: parser units per format, dry run creates nothing, undo removes the
  batch only.

### 25. Full account export

Deleting the account (`DELETE /api/auth/me`) is one click with a password, and
there is no way to take the data along first. The entries CSV covers only
entries.

- `GET /api/account/export` returns a zip with one JSON file per table of the
  user's data (settings, clients, projects, entries, invoices with lines and
  taxes) plus every invoice PDF.
- The delete dialog in `DeleteAccount.vue` offers it first.
- Import of such a file into an empty account: later, and only if someone
  needs to move between instances.
- Tricky: PDFs are rendered on the fly by `render_invoice_pdf`. Rendering a
  few hundred is a few seconds; fine in one request, with a streaming zip
  (`zipfile` on a spooled temporary file).
- Tests: the zip lists the expected files and contains only the user's rows.

### 26. Locked periods

Entries can be changed until they are invoiced. Non-billable time (the
"Admin" project) is never invoiced, so last year's records can always be
edited, as can billable time not yet billed. People who report hours to an
agency or a tax office want to close a month.

- Data: `locked_until` (a date) on `User`.
- `create_entry`, `update_entry`, `delete_entry`, bulk changes, `set_cell`
  and the timer's stop time refuse anything that starts on or before the date
  (in the local zone from item 1). The error says how to unlock.
- Settings: "Lock time up to" with a date. Unlocking is allowed; it is the
  user's own data, and the point is to avoid accidents.
- The timesheet greys out locked days.
- Tests: each write path refuses locked days, unlocking re-enables them.

### 27. Week start, date and number formats

The week starts on Monday everywhere (`week_start` in `services/timesheet.py`,
`mondayOf` in `web/src/lib/week.ts`), and the web app formats dates, times and
money with a fixed `en-GB` locale (`web/src/lib/format.ts`). Someone in the
US sees "24 Oct 2026" and a Monday week; someone in Germany sees "£1,234.50"
style separators on EUR amounts.

- Settings: `week_starts_on` (Monday or Sunday) and `locale` (a short list,
  default from the browser on signup).
- The grid and the weekly target use the setting on both sides; the API's
  `build_week` gets the day from the user.
- `format.ts` reads the locale from the auth store; the Vitest specs already
  pin a time zone and should pin a locale too.
- PDF dates and amounts follow the locale (`format_money` in
  `services/money.py`), which overlaps item 28.
- Tricky: a week starting on Sunday changes which entries belong to "this
  week" on the dashboard and in the target. Make that one helper.
- Tests: `week.spec.ts` for Sunday weeks, `test_timesheet.py` for the API
  side, format specs per locale.

### 28. Invoice PDF: logo, language and layout

The PDF is one fixed A4 layout in English with Helvetica (`services/pdf.py`).
Common requests: a logo, US Letter paper, invoices in the client's language,
and a line for "reverse charge" or similar legal text.

- Data: `logo_path` and `paper_size` on `User`; `language` on `Client`
  (English, plus whatever translations are added; a small dictionary in
  `services/pdf_text.py`).
- Logo upload with a size and type check, stored on a volume like item 16's
  receipts.
- The labels ("Invoice", "Bill to", "Due", "Subtotal") come from the
  dictionary. Amounts use the locale from item 27.
- Fonts: Helvetica has no glyphs for many scripts. Bundle DejaVu Sans in the
  image and register it with ReportLab.
- Depends on item 2: the PDF must render from stored values first.
- Tests: rendering with each language and paper size does not fail and
  contains the translated labels.

### 29. Accessibility pass

The app has some ARIA attributes (a few dozen across `web/src`) and keyboard
shortcuts, but no one has gone through it with a screen reader or keyboard
only. Likely gaps from reading the code:

- `GridCell.vue` inputs need labels that say the project and the day, not
  just the value, and errors announced with `aria-live`.
- `ModalDialog.vue` should trap focus and return it to the opener.
- `ToastHost.vue` should be a live region.
- `RevenueChart.vue` needs a text alternative (the numbers as a table).
- Colour is the only signal for project colours and status badges; add text.
- Contrast in dark mode (`lib/theme.ts`).
- Tests: Vitest specs for the labels and focus handling; an axe check would
  need a browser (item 30).

### 30. Browser end-to-end tests

The web specs mount components with mocked API calls, and the API tests call
routes directly. Nothing checks that the real build talks to the real API:
the proxy paths in `nginx.conf`, the PDF download link, the token handling in
`web/src/api/client.ts` on a 401.

- Playwright in `web/e2e`, against the compose stack with `SEED_DEMO=true`.
  A handful of flows: sign in as the demo user, start and stop the timer, type
  into the grid, generate a draft invoice and download its PDF, sign out.
- A separate CI job after `docker`, since it needs the images. It uses its
  own `WEB_PORT`.
- Keep it to these flows; everything else stays in unit and route tests.
- Tricky: the demo data depends on today's date (six months back from now).
  Assert on structure, not on numbers.
- Tests: this item is the tests.

### 31. Metrics and a readiness check

`/api/health` checks the database and the logs have one line per request with
a duration. For someone running this for a small team of freelancers (or just
on a home server), basic numbers would help: request rate, errors, slow
routes, and how long invoice generation and PDF rendering take.

- `/api/metrics` in Prometheus text format, off unless `METRICS_ENABLED=true`
  and only on the API port (nginx does not proxy it). Request counts and
  latency histograms by route template, not by raw path, so ids do not explode
  the label set.
- Health split: `/api/health` (process up) and `/api/ready` (database and
  migrations at head, compared with Alembic's current revision).
- Tests: metrics disabled by default, counters move after a request, ready
  fails on a pending migration.

## Maybe

### 32. Idle and forgotten-timer reminders

The timer can be stopped at the time you really finished, and
`LongTimerNotice.vue` prompts after 10 hours (`LIMIT_SECONDS`). Short gaps (a
two hour lunch with the timer on) are not caught, and nothing reminds anyone
to start the timer in the first place.

- Browser only, no server work: with the Idle Detection API where the browser
  has it (Chromium, behind a permission), or a simple "no input in this tab for
  N minutes" check, offer "You were away from 12:10. Keep, discard or split
  that time?". Discard stops the timer at 12:10 through the existing
  `ended_at` on `/api/timer/stop`; split stops and starts again.
- An optional desktop notification during working hours when no timer runs.
- Why Maybe: tab-level detection misses work done in other applications,
  which is most work. It may be more annoying than useful.
- Tests: a pure helper for the away decision in `web/src/lib`, specs for the
  dialog.

### 33. Calendar day view

The entries list and the weekly grid show totals; there is no view of the day
as time blocks. Gaps and overlaps are easiest to see on a calendar, and
dragging a block is the quickest way to fix a forgotten stop.

- A `DayView.vue` with one column per day of the week and entries as blocks
  positioned by local start and end. Drag to create, drag edges to resize,
  click to edit in `EntryForm.vue`.
- Grid entries (`source="grid"`) have no real start time. Show them in a
  "no time of day" strip, not at 09:00.
- Writes go through the existing entry routes; locked and invoiced entries are
  not draggable.
- Why Maybe: pointer and touch dragging with snapping is a lot of front-end
  work, and most people fill time from the timer or the grid.
- Tests: the layout maths (overlapping blocks side by side) as a pure helper
  in `web/src/lib` with specs.

### 34. Personal API tokens

Everything goes through the web app's bearer token. Scripts (a shell alias to
start the timer, a stand-up summary, a status bar widget) would need the
password today.

- Data: `ApiToken` (`user_id`, `name`, `token_hash`, `scopes`, `last_used_at`,
  `revoked_at`). Shown once at creation, prefixed (`ts_...`) so leaks are easy
  to grep.
- Scopes: `read`, `timer`, `entries`. Invoices and settings are not
  reachable with a token.
- `deps.py` accepts either a session token (item 21) or an API token, and
  routes declare the scope they need.
- `docs/api.md` gets an example with `curl`.
- Depends on item 21 for the session model.
- Tests: scopes enforced per route, revoked tokens refused, hash stored only.

### 35. Faster with years of data

The demo has six months of entries and all queries are quick. Several paths
load every matching row into Python:

- the dashboard loads all unbilled billable entries with their projects to
  value them (`routers/dashboard.py`), and all sent invoices;
- `invoices_overview` loads every invoice of the user to count them by
  display status;
- `time_report` loads every entry in the range to group them; a year by
  project is tens of thousands of rows for someone tracking in small pieces;
- the entries CSV builds the whole file in a `StringIO`.

What to change, if it ever matters:

- Counts and sums in SQL with `GROUP BY` (the overview can compute `overdue`
  with a `CASE` on `due_date`).
- Valuing unbilled time needs per-entry rounding, which SQL can do with a
  ceiling division on the epoch seconds, as long as the rule stays in one
  place. That is the reason to leave it in Python until it hurts.
- A streaming CSV response.
- Tricky: proving it. Build a fixture of 50,000 entries with a bulk insert
  and assert on the number of rows fetched, not on timing.
- Why Maybe: one person's time does not grow very fast. Ten years at a
  hundred entries a month is 12,000 rows.

### 36. Totals across currencies

Every amount is kept per currency (`Amount.list_from` in the reports and
dashboard), which is correct but means a freelancer with GBP and EUR clients
never sees one revenue number.

- Data: an `ExchangeRate` table (`currency`, `rate_to_base`, `valid_on`)
  filled by hand in settings. No rate service; optional import of a CSV from
  the user's bank or central bank.
- Reports and the dashboard show a converted total in the account currency
  (`User.currency`) next to the per-currency amounts, labelled as an estimate,
  with the rate date used.
- Invoices never change: they stay in the client's currency.
- Why Maybe: rates by hand are tedious, and a wrong rate silently produces a
  wrong total. The per-currency view is honest as it is.
- Tests: conversion picks the latest rate on or before the date; missing rate
  shows no total rather than a wrong one.

### 37. Read-only invoice links for clients

Some invoicing tools give the client a link to view the invoice and its time
details instead of an attachment.

- A random, revocable link per invoice (`InvoiceShare`: `token_hash`,
  `expires_at`, `revoked_at`) that serves the PDF and an HTML view without
  signing in. Optionally with the entries (date, hours, description) behind
  the invoice.
- Rate limited and never indexed (`X-Robots-Tag: noindex`).
- Depends on item 2: the shared view must show the stored details.
- Why Maybe: an unauthenticated route onto financial documents. The value
  over an emailed PDF (item 18) is small for a single freelancer.
- Tests: link works until revoked or expired, shows only that invoice.

### 38. Installable app with an offline timer

On a phone the app works in the browser, but starting the timer needs a
network round trip, and on a train it fails.

- A web manifest and a service worker that caches the built assets.
- Timer start and stop queued in IndexedDB when offline and sent when the
  connection returns, using the client's timestamps (the API accepts
  `ended_at` for stops; starts would need a `started_at` on `/api/timer/start`,
  checked against now).
- Why Maybe: offline writes mean conflicts (a timer started on the laptop
  while the phone was offline), and the one-running-timer index
  (`uq_time_entries_one_running`) would reject the replay. That needs a
  merge rule I do not have yet.
- Tests: the queue and replay logic as a pure module with specs.
