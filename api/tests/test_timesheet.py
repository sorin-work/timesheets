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
