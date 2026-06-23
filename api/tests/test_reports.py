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


def test_time_report_by_month(client, auth, two_clients):
    acme, _ = two_clients
    log(client, auth, acme["id"], "2026-01-31T09:00:00Z", "2026-01-31T10:00:00Z")
    log(client, auth, acme["id"], "2026-02-02T09:00:00Z", "2026-02-02T09:30:00Z")
    report = client.get(
        "/api/reports/time?from=2026-01-01&to=2026-02-28&group_by=month", headers=auth
    ).json()
    assert [(r["key"], r["tracked_seconds"]) for r in report["rows"]] == [
        ("2026-01", 3600),
        ("2026-02", 1800),
    ]


def test_revenue_report(client, auth, two_clients):
    acme, _ = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T11:00:00Z")
    inv = client.post(
        "/api/invoices/generate",
        json={
            "client_id": acme["client_id"],
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "issue_date": "2026-01-31",
        },
        headers=auth,
    ).json()
    report = client.get("/api/reports/revenue?year=2026", headers=auth).json()
    assert report["invoiced"] == []  # drafts do not count

    client.post(f"/api/invoices/{inv['id']}/send", headers=auth)
    client.post(f"/api/invoices/{inv['id']}/pay", json={"paid_on": "2026-02-14"}, headers=auth)
    report = client.get("/api/reports/revenue?year=2026", headers=auth).json()
    assert len(report["months"]) == 12
    assert report["months"][0]["invoiced"] == [{"currency": "EUR", "amount": "200.00"}]
    assert report["months"][0]["paid"] == []
    assert report["months"][1]["paid"] == [{"currency": "EUR", "amount": "200.00"}]
    assert report["paid"] == [{"currency": "EUR", "amount": "200.00"}]


def test_time_report_by_project_counts_unbilled_time(client, auth, two_clients):
    acme, bolt = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    log(client, auth, bolt["id"], "2026-01-05T11:00:00Z", "2026-01-05T12:00:00Z")
    client.post(
        "/api/invoices/generate",
        json={
            "client_id": acme["client_id"],
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
        },
        headers=auth,
    )
    report = client.get(
        "/api/reports/time?from=2026-01-01&to=2026-01-31&group_by=project", headers=auth
    ).json()
    rows = {r["label"]: r for r in report["rows"]}
    assert rows["Acme / Acme site"]["unbilled_seconds"] == 0
    assert rows["Bolt / Bolt site"]["unbilled_seconds"] == 3600


def test_report_validation(client, auth):
    assert (
        client.get("/api/reports/time?from=2026-02-01&to=2026-01-01", headers=auth).status_code
        == 422
    )
    assert (
        client.get("/api/reports/time?from=2020-01-01&to=2026-01-01", headers=auth).status_code
        == 422
    )
    assert client.get("/api/reports/time?from=2026-01-01", headers=auth).status_code == 422
    assert client.get("/api/reports/revenue?year=1999", headers=auth).status_code == 422


def test_reports_only_include_own_entries(client, auth, other_auth, two_clients):
    acme, _ = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    report = client.get("/api/reports/time?from=2026-01-01&to=2026-01-31", headers=other_auth)
    assert report.json()["rows"] == []


def test_time_report_for_one_client(client, auth, two_clients):
    acme, bolt = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:00:00Z")
    log(client, auth, bolt["id"], "2026-01-06T09:00:00Z", "2026-01-06T10:00:00Z")
    report = client.get(
        f"/api/reports/time?from=2026-01-01&to=2026-01-31&group_by=month&client_id={bolt['client_id']}",
        headers=auth,
    ).json()
    assert [(r["key"], r["tracked_seconds"]) for r in report["rows"]] == [("2026-01", 3600)]
    assert report["amounts"] == [{"currency": "USD", "amount": "80.00"}]


def test_time_report_csv(client, auth, two_clients):
    acme, bolt = two_clients
    log(client, auth, acme["id"], "2026-01-05T09:00:00Z", "2026-01-05T10:30:00Z")
    log(client, auth, bolt["id"], "2026-01-06T09:00:00Z", "2026-01-06T10:00:00Z", billable=False)
    r = client.get("/api/reports/time.csv?from=2026-01-01&to=2026-01-31", headers=auth)
    assert r.status_code == 200
    assert "time-by-client-2026-01-01-2026-01-31.csv" in r.headers["content-disposition"]
    assert r.text.splitlines() == [
        "client,tracked_hours,billable_hours,unbilled_hours,currency,value",
        "Acme,1.50,1.50,1.50,EUR,150.00",
        "Bolt,1.00,0.00,0.00,,0.00",
    ]
