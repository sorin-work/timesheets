import pytest


@pytest.fixture
def two_clients(client, auth):
    def make(name, currency, rate):
        c = client.post(
            "/api/clients",
            json={"name": name, "currency": currency, "hourly_rate": rate},
            headers=auth,
        ).json()
        return client.post(
            "/api/projects", json={"client_id": c["id"], "name": f"{name} site"}, headers=auth
        ).json()

    return make("Acme", "EUR", "100"), make("Bolt", "USD", "80")


def log(client, auth, project_id, start, end, billable=True):
    r = client.post(
        "/api/entries",
        json={"project_id": project_id, "started_at": start, "ended_at": end, "billable": billable},
        headers=auth,
    )
    assert r.status_code == 201


def test_time_report_by_client(client, auth, two_clients):
    acme, bolt = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T11:00:00Z")
    log(client, auth, acme["id"], "2026-01-06T09:00:00Z", "2026-01-06T09:30:00Z", billable=False)
    log(client, auth, bolt["id"], "2026-01-07T09:00:00Z", "2026-01-07T10:30:00Z")

    r = client.get("/api/reports/time?from=2026-01-01&to=2026-01-31", headers=auth)
    assert r.status_code == 200, r.text
    report = r.json()
    assert [row["label"] for row in report["rows"]] == ["Acme", "Bolt"]
    acme_row, bolt_row = report["rows"]
    assert acme_row["tracked_seconds"] == 9000
    assert acme_row["billable_seconds"] == 7200
    assert acme_row["amounts"] == [{"currency": "EUR", "amount": "200.00"}]
    assert bolt_row["amounts"] == [{"currency": "USD", "amount": "120.00"}]
    assert report["tracked_seconds"] == 14400
    assert report["amounts"] == [
        {"currency": "EUR", "amount": "200.00"},
        {"currency": "USD", "amount": "120.00"},
    ]
