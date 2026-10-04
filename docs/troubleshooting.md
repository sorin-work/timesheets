# Troubleshooting

**The api container keeps restarting.** Look at `docker compose logs api`. The
usual cause is a wrong `DATABASE_URL` or a database that is not ready yet; the
compose file waits for the Postgres healthcheck, but an external database has
to be reachable from the container.

**`alembic upgrade head` fails after pulling.** Someone added a migration with
the same parent as yours. Run `alembic heads`; if there are two, rebase your
migration's `down_revision` onto the other one.

**Tests fail with "database ... does not exist".** The API tests need their own
empty database and drop and recreate the `public` schema in it. Create one and
point `TEST_DATABASE_URL` at it; never use a database with data you care about.

**Entries show up on the wrong day in the timesheet.** Check the time zone in
Settings. Days are decided by the time zone saved there, not by the browser.

**The invoice hours are higher than the tracked hours.** That is the rounding
rule from Settings, applied per entry and always up. A 7 minute entry is 0.2 h
with 6 minute rounding and 0.25 h with 15 minute rounding.

**I cannot edit or delete an entry.** It is on an invoice. Delete the draft
invoice to release its entries; sent and paid invoices are final (move a sent
invoice back to draft first if it was never really sent).

**The PDF link says "Not authenticated".** The link carries your current access
token; sign in again if it has expired (after `TOKEN_TTL_MINUTES`).

**Too many attempts (429) when signing in.** Sign in and sign up are limited to
10 attempts per 5 minutes; wait for the time in the `Retry-After` header.
