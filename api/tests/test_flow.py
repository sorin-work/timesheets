"""One freelancer's month, end to end through the API."""

from datetime import date

from timesheets import clock


def test_track_invoice_and_get_paid(client, monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: date(2026, 10, 5))
    token = client.post(
        "/api/auth/signup",
        json={"email": "flow@example.com", "password": "password123", "name": "Flo"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    client.patch(
        "/api/settings",
        json={"rounding": "15", "timezone": "Europe/Berlin", "invoice_prefix": "FL-"},
        headers=h,
    )
    acme = client.post(
        "/api/clients", json={"name": "Acme GmbH", "hourly_rate": "80"}, headers=h
    ).json()
    site = client.post(
        "/api/projects", json={"client_id": acme["id"], "name": "Shop"}, headers=h
    ).json()

    # Grid: 2:10 on Tuesday 1 Sep (local), manual entry 50 min on Wednesday
    client.put(
        "/api/timesheet/cell",
        json={"project_id": site["id"], "date": "2026-09-01", "minutes": 130},
        headers=h,
    )
    client.post(
        "/api/entries",
        json={
            "project_id": site["id"],
            "started_at": "2026-09-02T07:00:00Z",
            "ended_at": "2026-09-02T07:50:00Z",
            "description": "Checkout",
        },
        headers=h,
    )
    week = client.get("/api/timesheet?week=2026-09-01", headers=h).json()
    assert week["totals"][1:3] == [130 * 60, 50 * 60]

    preview = client.get(
        "/api/invoices/unbilled",
        params={"client_id": acme["id"], "period_start": "2026-09-01", "period_end": "2026-09-30"},
        headers=h,
    ).json()
    assert preview["projects"][0]["billable_seconds"] == (135 + 60) * 60

    invoice = client.post(
        "/api/invoices/generate",
        json={
            "client_id": acme["id"],
            "period_start": "2026-09-01",
            "period_end": "2026-09-30",
            "issue_date": "2026-10-01",
            "taxes": [{"name": "USt", "rate": "19"}],
        },
        headers=h,
    ).json()
    assert invoice["number"] == "FL-1"
    assert invoice["subtotal"] == "260.00"  # 3.25 h x 80
    assert invoice["total"] == "309.40"

    client.post(f"/api/invoices/{invoice['id']}/send", headers=h)
    client.post(f"/api/invoices/{invoice['id']}/pay", json={"paid_on": "2026-10-04"}, headers=h)

    revenue = client.get("/api/reports/revenue?year=2026", headers=h).json()
    assert revenue["months"][9]["invoiced"] == [{"currency": "EUR", "amount": "309.40"}]
    assert revenue["months"][9]["paid"] == [{"currency": "EUR", "amount": "309.40"}]
    report = client.get("/api/reports/time?from=2026-09-01&to=2026-09-30", headers=h).json()
    assert report["rows"][0]["unbilled_seconds"] == 0
    assert client.get(f"/api/invoices/{invoice['id']}/pdf", headers=h).status_code == 200
