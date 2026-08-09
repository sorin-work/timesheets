def log(client, auth, project_id, start, end):
    r = client.post(
        "/api/entries",
        json={"project_id": project_id, "started_at": start, "ended_at": end},
        headers=auth,
    )
    assert r.status_code == 201, r.text


def test_week_groups_seconds_by_project_and_day(client, auth, project):
    other = client.post(
        "/api/projects", json={"client_id": project["client_id"], "name": "Ops"}, headers=auth
    ).json()
    log(client, auth, project["id"], "2025-12-08T09:00:00Z", "2025-12-08T11:00:00Z")
    log(client, auth, project["id"], "2025-12-08T13:00:00Z", "2025-12-08T13:30:00Z")
    log(client, auth, project["id"], "2025-12-10T09:00:00Z", "2025-12-10T10:00:00Z")
    log(client, auth, other["id"], "2025-12-14T20:00:00Z", "2025-12-14T20:45:00Z")
    log(client, auth, other["id"], "2025-12-15T09:00:00Z", "2025-12-15T10:00:00Z")  # next week

    sheet = client.get("/api/timesheet?week=2025-12-11", headers=auth).json()
    assert sheet["week_start"] == "2025-12-08"
    assert sheet["days"][0] == "2025-12-08"
    assert sheet["days"][-1] == "2025-12-14"
    assert [r["project_name"] for r in sheet["rows"]] == ["Ops", "Website"]
    ops, website = sheet["rows"]
    assert website["seconds"] == [9000, 0, 3600, 0, 0, 0, 0]
    assert ops["seconds"] == [0, 0, 0, 0, 0, 0, 2700]
    assert sheet["totals"] == [9000, 0, 3600, 0, 0, 0, 2700]
    assert sheet["total"] == 15300


def test_empty_week(client, auth):
    sheet = client.get("/api/timesheet?week=2025-12-08", headers=auth).json()
    assert sheet["rows"] == []
    assert sheet["totals"] == [0] * 7


def cell(client, auth, project_id, day, minutes):
    return client.put(
        "/api/timesheet/cell",
        json={"project_id": project_id, "date": day, "minutes": minutes},
        headers=auth,
    )


def website_row(sheet):
    return next(r for r in sheet["rows"] if r["project_name"] == "Website")


def test_set_cell_creates_and_resizes_a_grid_entry(client, auth, project):
    r = cell(client, auth, project["id"], "2025-12-09", 90)
    assert r.status_code == 200, r.text
    assert website_row(r.json())["seconds"][1] == 5400

    r = cell(client, auth, project["id"], "2025-12-09", 30)
    assert website_row(r.json())["seconds"][1] == 1800
    entries = client.get("/api/entries", headers=auth).json()["items"]
    assert len(entries) == 1
    assert entries[0]["source"] == "grid"


def test_set_cell_keeps_tracked_entries(client, auth, project):
    log(client, auth, project["id"], "2025-12-09T08:00:00Z", "2025-12-09T09:00:00Z")
    r = cell(client, auth, project["id"], "2025-12-09", 150)
    assert website_row(r.json())["seconds"][1] == 9000
    sources = sorted(e["source"] for e in client.get("/api/entries", headers=auth).json()["items"])
    assert sources == ["grid", "manual"]

    r = cell(client, auth, project["id"], "2025-12-09", 30)
    assert r.status_code == 422


def test_clearing_a_cell_removes_the_grid_entry(client, auth, project):
    cell(client, auth, project["id"], "2025-12-09", 60)
    r = cell(client, auth, project["id"], "2025-12-09", 0)
    assert r.json()["rows"] == []


def test_days_follow_the_users_time_zone(client, auth, project):
    client.patch("/api/settings", json={"timezone": "Europe/Bucharest"}, headers=auth)
    # 01:30 on Tuesday in Bucharest (UTC+3 in summer)
    log(client, auth, project["id"], "2026-04-20T22:30:00Z", "2026-04-20T23:30:00Z")
    # 00:30 on Monday 27 April in Bucharest: next week, even though it is Sunday in UTC
    log(client, auth, project["id"], "2026-04-26T21:30:00Z", "2026-04-26T22:00:00Z")

    sheet = client.get("/api/timesheet?week=2026-04-20", headers=auth).json()
    assert website_row(sheet)["seconds"] == [0, 3600, 0, 0, 0, 0, 0]
    next_week = client.get("/api/timesheet?week=2026-04-27", headers=auth).json()
    assert website_row(next_week)["seconds"][0] == 1800


def test_grid_entries_are_created_on_the_local_day(client, auth, project):
    client.patch("/api/settings", json={"timezone": "Pacific/Auckland"}, headers=auth)
    r = cell(client, auth, project["id"], "2026-04-21", 60)
    assert website_row(r.json())["seconds"][1] == 3600
    created = client.get("/api/entries", headers=auth).json()["items"][0]
    assert created["started_at"] == "2026-04-20T21:00:00Z"  # 09:00 in Auckland


def test_invoiced_grid_time_is_kept_when_the_cell_changes(client, auth, project):
    client.patch(f"/api/clients/{project['client_id']}", json={"hourly_rate": "50"}, headers=auth)
    cell(client, auth, project["id"], "2026-08-04", 120)
    client.post(
        "/api/invoices/generate",
        json={
            "client_id": project["client_id"],
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
        },
        headers=auth,
    )
    assert cell(client, auth, project["id"], "2026-08-04", 60).status_code == 422
    r = cell(client, auth, project["id"], "2026-08-04", 180)
    assert website_row(r.json())["seconds"][1] == 3 * 3600
    sources = sorted(
        (e["source"], e["invoice_id"] is not None)
        for e in client.get("/api/entries", headers=auth).json()["items"]
    )
    assert sources == [("grid", False), ("grid", True)]


def test_cell_validation(client, auth, project, other_auth):
    assert cell(client, auth, project["id"], "2026-08-04", -1).status_code == 422
    assert cell(client, auth, project["id"], "2026-08-04", 24 * 60 + 1).status_code == 422
    assert cell(client, other_auth, project["id"], "2026-08-04", 30).status_code == 404
