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
