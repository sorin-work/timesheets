import pytest


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
