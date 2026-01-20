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


def test_invoiced_entries_cannot_be_changed(client, auth, draft):
    entry = client.get("/api/entries", headers=auth).json()["items"][0]
    assert entry["invoice_id"] == draft["id"]
    r = client.patch(f"/api/entries/{entry['id']}", json={"description": "x"}, headers=auth)
    assert r.status_code == 409
    assert client.delete(f"/api/entries/{entry['id']}", headers=auth).status_code == 409


def test_already_invoiced_time_is_not_billed_twice(client, auth, billed_client, draft):
    r = generate(client, auth, billed_client["client"]["id"])
    assert r.status_code == 422


def test_non_billable_and_running_entries_are_skipped(client, auth, billed_client):
    site = billed_client["site"]["id"]
    log(client, auth, site, "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z", billable=False)
    client.post("/api/timer/start", json={"project_id": site}, headers=auth)
    assert generate(client, auth, billed_client["client"]["id"]).status_code == 422


def test_group_by_entry_lists_each_entry(client, auth, billed_client):
    site = billed_client["site"]["id"]
    log(client, auth, site, "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z", description="Header")
    log(client, auth, site, "2026-01-06T09:00:00Z", "2026-01-06T09:30:00Z")
    invoice = generate(client, auth, billed_client["client"]["id"], group_by="entry").json()
    assert [li["description"] for li in invoice["lines"]] == [
        "2026-01-05 Header",
        "2026-01-06 Website",
    ]
    assert invoice["subtotal"] == "150.00"


def test_rounding_is_applied_per_entry(client, auth, billed_client):
    client.patch("/api/settings", json={"rounding": "15"}, headers=auth)
    site = billed_client["site"]["id"]
    log(client, auth, site, "2026-01-05T09:00:00Z", "2026-01-05T09:20:00Z")  # 20 -> 30 min
    log(client, auth, site, "2026-01-06T09:00:00Z", "2026-01-06T09:05:00Z")  # 5 -> 15 min
    invoice = generate(client, auth, billed_client["client"]["id"]).json()
    assert invoice["lines"][0]["quantity"] == "0.75"
    assert invoice["subtotal"] == "75.00"


def test_generate_for_selected_projects_only(client, auth, billed_client):
    log(client, auth, billed_client["site"]["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    log(client, auth, billed_client["audit"]["id"], "2026-01-05T11:00:00Z", "2026-01-05T12:00:00Z")
    invoice = generate(
        client, auth, billed_client["client"]["id"], project_ids=[billed_client["audit"]["id"]]
    ).json()
    assert [li["description"] for li in invoice["lines"]] == ["Audit"]
    # The website hour is still unbilled
    rest = generate(client, auth, billed_client["client"]["id"]).json()
    assert [li["description"] for li in rest["lines"]] == ["Website"]
    assert rest["number"] == "INV-2"


def test_only_entries_inside_the_period_are_billed(client, auth, billed_client):
    site = billed_client["site"]["id"]
    log(client, auth, site, "2025-12-31T09:00:00Z", "2025-12-31T10:00:00Z")
    log(client, auth, site, "2026-01-31T09:00:00Z", "2026-01-31T10:00:00Z")
    log(client, auth, site, "2026-02-01T09:00:00Z", "2026-02-01T10:00:00Z")
    invoice = generate(client, auth, billed_client["client"]["id"]).json()
    assert invoice["entry_count"] == 1


def test_project_without_any_rate_cannot_be_invoiced(client, auth):
    norate = client.post("/api/clients", json={"name": "Pro bono"}, headers=auth).json()
    p = client.post("/api/projects", json={"client_id": norate["id"], "name": "X"}, headers=auth)
    log(client, auth, p.json()["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    r = generate(client, auth, norate["id"])
    assert r.status_code == 422
    assert "hourly rate" in r.json()["error"]["message"]


def test_generate_validation(client, auth, billed_client, other_auth):
    cid = billed_client["client"]["id"]
    r = generate(client, auth, cid, period_start="2026-02-01", period_end="2026-01-01")
    assert r.status_code == 422
    assert generate(client, auth, cid, group_by="client").status_code == 422
    assert generate(client, other_auth, cid).status_code == 404


def test_invoices_are_private(client, auth, other_auth, draft):
    assert client.get(f"/api/invoices/{draft['id']}", headers=other_auth).status_code == 404
    assert client.post(f"/api/invoices/{draft['id']}/send", headers=other_auth).status_code == 404
    assert client.delete(f"/api/invoices/{draft['id']}", headers=other_auth).status_code == 404
    assert client.get("/api/invoices", headers=other_auth).json() == []


def test_invoice_currency_comes_from_the_client(client, auth):
    gbp = client.post(
        "/api/clients",
        json={"name": "UK Ltd", "currency": "GBP", "hourly_rate": "70"},
        headers=auth,
    ).json()
    p = client.post("/api/projects", json={"client_id": gbp["id"], "name": "X"}, headers=auth)
    log(client, auth, p.json()["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    assert generate(client, auth, gbp["id"]).json()["currency"] == "GBP"


def test_invoice_pdf(client, auth, draft):
    client.patch(
        "/api/settings",
        json={
            "business_name": "Fran Dev",
            "business_address": "1 Main St\nCluj",
            "tax_id": "RO123",
        },
        headers=auth,
    )
    r = client.get(f"/api/invoices/{draft['id']}/pdf", headers=auth)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert 'filename="INV-1.pdf"' in r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")


def test_invoice_pdf_accepts_token_in_query(client, auth, draft):
    token = auth["Authorization"].split()[1]
    r = client.get(f"/api/invoices/{draft['id']}/pdf?token={token}")
    assert r.status_code == 200
    assert client.get(f"/api/invoices/{draft['id']}/pdf").status_code == 401


def test_filter_and_sort_invoices(client, auth, billed_client):
    cid = billed_client["client"]["id"]
    site = billed_client["site"]["id"]
    numbers = []
    for day, hours in (("05", 1), ("06", 3), ("07", 2)):
        log(client, auth, site, f"2026-01-{day}T09:00:00Z", f"2026-01-{day}T1{hours - 1}:00:00Z")
        inv = generate(
            client,
            auth,
            cid,
            period_start=f"2026-01-{day}",
            period_end=f"2026-01-{day}",
            issue_date=f"2026-01-{int(day) + 5:02d}",
        ).json()
        numbers.append(inv["number"])
    client.post("/api/invoices/1/send", headers=auth)
    client.post("/api/invoices/2/send", headers=auth)
    client.patch("/api/invoices/3", json={"due_date": "2026-03-01"}, headers=auth)

    def listed(query=""):
        return [i["number"] for i in client.get(f"/api/invoices?{query}", headers=auth).json()]

    assert listed() == ["INV-3", "INV-2", "INV-1"]
    assert listed("order=asc") == ["INV-1", "INV-2", "INV-3"]
    assert listed("sort=total&order=desc") == ["INV-2", "INV-3", "INV-1"]
    assert listed("sort=issue_date&order=asc") == ["INV-1", "INV-2", "INV-3"]
    assert listed("status=draft") == ["INV-3"]
    assert listed("status=overdue") == ["INV-2", "INV-1"]
    assert listed("status=sent") == []
    client.patch("/api/invoices/3", json={"issue_date": "2026-02-01"}, headers=auth)
    client.post("/api/invoices/3/send", headers=auth)
    assert listed("status=sent") == ["INV-3"]
    assert listed(f"client_id={cid}&status=paid") == []
    assert client.get("/api/invoices?sort=client", headers=auth).status_code == 422
