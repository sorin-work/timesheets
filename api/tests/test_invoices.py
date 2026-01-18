from datetime import date

import pytest

from timesheets import clock


@pytest.fixture(autouse=True)
def pinned_today(monkeypatch):
    """Invoices in these tests are issued on 2026-02-01; pretend it is a few days later."""
    monkeypatch.setattr(clock, "today", lambda: date(2026, 2, 5))


@pytest.fixture
def billed_client(client, auth):
    acme = client.post(
        "/api/clients", json={"name": "Acme", "hourly_rate": "100.00"}, headers=auth
    ).json()
    site = client.post(
        "/api/projects", json={"client_id": acme["id"], "name": "Website"}, headers=auth
    ).json()
    audit = client.post(
        "/api/projects",
        json={"client_id": acme["id"], "name": "Audit", "hourly_rate": "150.00"},
        headers=auth,
    ).json()
    return {"client": acme, "site": site, "audit": audit}


def log(client, auth, project_id, start, end, **kw):
    r = client.post(
        "/api/entries",
        json={"project_id": project_id, "started_at": start, "ended_at": end, **kw},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    return r.json()


def generate(client, auth, client_id, **kw):
    payload = {
        "client_id": client_id,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "issue_date": "2026-02-01",
        **kw,
    }
    return client.post("/api/invoices/generate", json=payload, headers=auth)


def test_generate_invoice_groups_unbilled_time_by_project(client, auth, billed_client):
    site, audit = billed_client["site"]["id"], billed_client["audit"]["id"]
    log(client, auth, site, "2026-01-05T09:00:00Z", "2026-01-05T11:30:00Z")
    log(client, auth, site, "2026-01-06T09:00:00Z", "2026-01-06T10:00:00Z")
    log(client, auth, audit, "2026-01-07T09:00:00Z", "2026-01-07T09:45:00Z")

    r = generate(client, auth, billed_client["client"]["id"])
    assert r.status_code == 201, r.text
    invoice = r.json()
    assert invoice["number"] == "INV-1"
    assert invoice["status"] == "draft"
    assert invoice["due_date"] == "2026-02-15"
    assert invoice["entry_count"] == 3
    lines = [(li["description"], li["quantity"], li["amount"]) for li in invoice["lines"]]
    assert lines == [("Audit", "0.75", "112.50"), ("Website", "3.50", "350.00")]
    assert invoice["subtotal"] == "462.50"
    assert invoice["total"] == "462.50"


def test_tax_lines_are_added_to_the_total(client, auth, billed_client):
    site = billed_client["site"]["id"]
    log(client, auth, site, "2026-01-05T09:00:00Z", "2026-01-05T12:00:00Z")
    r = generate(
        client,
        auth,
        billed_client["client"]["id"],
        taxes=[{"name": "VAT", "rate": "19"}, {"name": "Withholding", "rate": "10"}],
    )
    invoice = r.json()
    assert invoice["subtotal"] == "300.00"
    assert [(t["name"], t["amount"]) for t in invoice["taxes"]] == [
        ("VAT", "57.00"),
        ("Withholding", "30.00"),
    ]
    assert invoice["tax_total"] == "87.00"
    assert invoice["total"] == "387.00"


def test_tax_rate_validation(client, auth, billed_client):
    log(client, auth, billed_client["site"]["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    for tax in ({"name": "", "rate": "5"}, {"name": "VAT", "rate": "101"}):
        r = generate(client, auth, billed_client["client"]["id"], taxes=[tax])
        assert r.status_code == 422


@pytest.fixture
def draft(client, auth, billed_client):
    log(client, auth, billed_client["site"]["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    return generate(client, auth, billed_client["client"]["id"]).json()


def test_invoice_status_flow(client, auth, draft):
    url = f"/api/invoices/{draft['id']}"
    assert client.post(f"{url}/pay", headers=auth).status_code == 409

    sent = client.post(f"{url}/send", headers=auth).json()
    assert sent["status"] == "sent"
    assert sent["sent_at"] is not None

    paid = client.post(f"{url}/pay", json={"paid_on": "2026-02-10"}, headers=auth).json()
    assert paid["status"] == "paid"
    assert paid["paid_at"].startswith("2026-02-10")

    assert client.post(f"{url}/send", headers=auth).status_code == 409
    unpaid = client.post(f"{url}/unpay", headers=auth).json()
    assert unpaid["status"] == "sent"
    assert unpaid["paid_at"] is None

    reverted = client.post(f"{url}/revert", headers=auth).json()
    assert reverted["status"] == "draft"


def test_sent_invoice_past_its_due_date_is_overdue(client, auth, billed_client):
    log(client, auth, billed_client["site"]["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    old = generate(client, auth, billed_client["client"]["id"], issue_date="2020-01-01").json()
    client.post(f"/api/invoices/{old['id']}/send", headers=auth)
    assert client.get(f"/api/invoices/{old['id']}", headers=auth).json()["status"] == "overdue"

    log(client, auth, billed_client["site"]["id"], "2026-01-06T09:00:00Z", "2026-01-06T10:00:00Z")
    new = generate(client, auth, billed_client["client"]["id"], issue_date="2026-02-01").json()
    client.post(f"/api/invoices/{new['id']}/send", headers=auth)
    assert client.get(f"/api/invoices/{new['id']}", headers=auth).json()["status"] == "sent"

    statuses = {i["number"]: i["status"] for i in client.get("/api/invoices", headers=auth).json()}
    assert statuses == {old["number"]: "overdue", new["number"]: "sent"}

    paid = client.post(f"/api/invoices/{old['id']}/pay", headers=auth).json()
    assert paid["status"] == "paid"


def test_edit_draft_invoice(client, auth, draft):
    r = client.patch(
        f"/api/invoices/{draft['id']}",
        json={
            "notes": "Thanks!",
            "due_date": "2026-03-01",
            "taxes": [{"name": "VAT", "rate": "20"}],
        },
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["notes"] == "Thanks!"
    assert body["due_date"] == "2026-03-01"
    assert body["tax_total"] == "20.00"
    assert body["total"] == "120.00"

    r = client.patch(f"/api/invoices/{draft['id']}", json={"due_date": "2026-01-01"}, headers=auth)
    assert r.status_code == 422


def test_sent_invoices_are_locked(client, auth, draft):
    client.post(f"/api/invoices/{draft['id']}/send", headers=auth)
    assert (
        client.patch(f"/api/invoices/{draft['id']}", json={"notes": "x"}, headers=auth).status_code
        == 409
    )
    assert client.delete(f"/api/invoices/{draft['id']}", headers=auth).status_code == 409


def test_deleting_a_draft_releases_its_entries(client, auth, billed_client, draft):
    assert client.delete(f"/api/invoices/{draft['id']}", headers=auth).status_code == 204
    again = generate(client, auth, billed_client["client"]["id"])
    assert again.status_code == 201
    assert again.json()["entry_count"] == 1
