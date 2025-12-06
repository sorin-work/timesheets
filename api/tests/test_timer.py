def test_start_and_stop_timer(client, auth, project):
    assert client.get("/api/timer", headers=auth).json() is None

    r = client.post(
        "/api/timer/start",
        json={"project_id": project["id"], "description": "bugfix"},
        headers=auth,
    )
    assert r.status_code == 201
    started = r.json()
    assert started["running"] is True
    assert started["source"] == "timer"
    assert client.get("/api/timer", headers=auth).json()["id"] == started["id"]

    stopped = client.post("/api/timer/stop", headers=auth).json()
    assert stopped["running"] is False
    assert stopped["ended_at"] is not None
    assert client.get("/api/timer", headers=auth).json() is None


def test_starting_a_timer_stops_the_running_one(client, auth, project):
    first = client.post("/api/timer/start", json={"project_id": project["id"]}, headers=auth).json()
    second = client.post(
        "/api/timer/start", json={"project_id": project["id"], "description": "next"}, headers=auth
    ).json()
    closed = client.get(f"/api/entries/{first['id']}", headers=auth).json()
    assert closed["running"] is False
    assert closed["ended_at"] == second["started_at"]
    assert client.get("/api/timer", headers=auth).json()["id"] == second["id"]


def test_update_running_timer(client, auth, project):
    client.post("/api/timer/start", json={"project_id": project["id"]}, headers=auth)
    r = client.patch(
        "/api/timer", json={"description": " writing tests ", "billable": False}, headers=auth
    )
    assert r.status_code == 200
    assert r.json()["description"] == "writing tests"
    assert r.json()["billable"] is False


def test_stop_without_running_timer(client, auth):
    r = client.post("/api/timer/stop", headers=auth)
    assert r.status_code == 409
    assert client.patch("/api/timer", json={"description": "x"}, headers=auth).status_code == 409


def test_timer_requires_an_active_project(client, auth, other_auth, project):
    r = client.post("/api/timer/start", json={"project_id": project["id"]}, headers=other_auth)
    assert r.status_code == 404
    client.post(f"/api/projects/{project['id']}/archive", headers=auth)
    r = client.post("/api/timer/start", json={"project_id": project["id"]}, headers=auth)
    assert r.status_code == 422


def test_timers_are_per_user(client, auth, other_auth, project):
    client.post("/api/timer/start", json={"project_id": project["id"]}, headers=auth)
    assert client.get("/api/timer", headers=other_auth).json() is None
