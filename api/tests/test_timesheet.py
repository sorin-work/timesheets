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
