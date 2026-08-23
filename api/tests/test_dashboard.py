from datetime import date

import pytest

from timesheets import clock


@pytest.fixture(autouse=True)
def pinned_today(monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: date(2026, 3, 4))  # a Wednesday


def log(client, auth, project_id, start, end, **kw):
    r = client.post(
        "/api/entries",
        json={"project_id": project_id, "started_at": start, "ended_at": end, **kw},
        headers=auth,
    )
    assert r.status_code == 201


def test_empty_dashboard(client, auth):
    body = client.get("/api/dashboard", headers=auth).json()
    assert body["week_seconds"] == 0
    assert body["unbilled"] == []
    assert body["recent"] == []


def test_dashboard_numbers(client, auth, project):
    log(client, auth, project["id"], "2026-03-04T08:00:00Z", "2026-03-04T09:30:00Z")
    log(client, auth, project["id"], "2026-03-02T08:00:00Z", "2026-03-02T09:00:00Z")
    log(client, auth, project["id"], "2026-02-27T08:00:00Z", "2026-02-27T09:00:00Z")
    log(client, auth, project["id"], "2026-02-26T08:00:00Z", "2026-02-26T10:00:00Z", billable=False)
    invoice = client.post(
        "/api/invoices/generate",
        json={
            "client_id": project["client_id"],
            "period_start": "2026-02-01",
            "period_end": "2026-02-28",
            "issue_date": "2026-02-28",
            "due_days": 2,
        },
        headers=auth,
    ).json()
    client.post(f"/api/invoices/{invoice['id']}/send", headers=auth)

    body = client.get("/api/dashboard", headers=auth).json()
    assert body["today_seconds"] == 5400
    assert body["week_seconds"] == 9000
    assert body["unbilled_seconds"] == 9000
    assert body["unbilled"] == [{"currency": "EUR", "amount": "250.00"}]
    assert body["outstanding"] == [{"currency": "EUR", "amount": "100.00"}]
    assert body["outstanding_count"] == 1
    assert body["overdue_count"] == 1
    assert len(body["recent"]) == 4


def test_dashboard_warns_about_budgets(client, auth, project):
    client.patch(f"/api/projects/{project['id']}", json={"budget_hours": "2"}, headers=auth)
    log(client, auth, project["id"], "2026-03-02T08:00:00Z", "2026-03-02T09:30:00Z")
    body = client.get("/api/dashboard", headers=auth).json()
    assert body["budgets"] == []
    log(client, auth, project["id"], "2026-03-03T08:00:00Z", "2026-03-03T09:00:00Z")
    warning = client.get("/api/dashboard", headers=auth).json()["budgets"][0]
    assert (warning["project_name"], warning["percent"], warning["budget_hours"]) == (
        "Website",
        125,
        "2.00",
    )
