# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-24

First stable release.

### Added

- Accounts with sign up, sign in, password change and account deletion;
  sign in and sign up are rate limited.
- Clients and projects with hourly rates, project rate overrides, hour budgets,
  colours, billable defaults, archiving and a client summary page.
- Running timer with task switching, continue-an-entry, keyboard shortcuts
  (Alt+S, Alt+N), the running time in the tab title and a prompt to stop a
  timer that ran for more than 10 hours at the right time.
- Manual time entries with filters kept in the URL, pagination, totals, CSV
  export and bulk billable/delete.
- Weekly timesheet grid in the user's time zone: type durations into cells,
  add project rows, copy last week's projects, arrow key navigation and a
  weekly target.
- Rounding rules (none, 6 or 15 minutes, rounded up per entry).
- Invoices generated from unbilled time with a preview, per-project or
  per-entry lines, extra lines (expenses, fees, discounts), tax lines with
  defaults from settings, reference/PO numbers, notes, payment details, PDF
  download and print view.
- Invoice statuses draft, sent, paid and overdue, with counts and totals per
  status, sorting and due/late labels.
- Reports by client, project or month with CSV download, and a monthly revenue
  chart of invoiced and paid amounts.
- Dashboard with today, this week, unbilled value, outstanding invoices, budget
  warnings and a getting started checklist.
- Dark mode, toasts, loading skeletons, phone layout, not found page.
- Docker Compose setup (Postgres, API, nginx) with healthchecks and a demo
  account, GitHub Actions CI, API reference and architecture notes.
- Request ids, JSON logs (`LOG_FORMAT=json`) and a health check that checks the
  database.

### Fixed

- Paging reported one page too few when the last page was partial.
- Entries already on a rounding step were billed one extra step.
- Timesheet days and grid edits used UTC instead of the user's time zone.
- Entries near midnight were listed under the wrong day in the web app.
- Tax lines rounded half to even and could be a cent short.
- Invoice PDFs could be downloaded by other accounts.
- Double-clicking "Create draft invoice" could bill the same time twice.
- Invoice notes were rendered as HTML.
- `INV-10` sorted below `INV-9` in the invoices list.
- Invoices showed as overdue on their due date.
- Editing a project accepted a negative hourly rate.
- Editing only an entry's end time could make it end before it started.
- Deleting a client with invoices returned a server error.
- Archiving a project left its timer running.
- `CORS_ORIGINS` could not be set as a comma separated list.
- The next account to sign in saw the previous account's projects.

[1.0.0]: https://github.com/sorin-work/timesheets/releases/tag/v1.0.0
