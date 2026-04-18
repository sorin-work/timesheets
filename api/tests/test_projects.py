def make_client(client, auth, **kw):
    payload = {"name": "Acme", "hourly_rate": "80.00", **kw}
    return client.post("/api/clients", json=payload, headers=auth).json()


def test_create_project_inherits_client_rate(client, auth):
    acme = make_client(client, auth, currency="GBP")
    r = client.post(
        "/api/projects", json={"client_id": acme["id"], "name": "Website"}, headers=auth
    )
    assert r.status_code == 201
    project = r.json()
    assert project["client_name"] == "Acme"
    assert project["hourly_rate"] is None
    assert project["effective_rate"] == "80.00"
    assert project["currency"] == "GBP"


def new_project(client, auth, client_id, **kw):
    r = client.post("/api/projects", json={"client_id": client_id, "name": "P", **kw}, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_project_rate_override_and_reset(client, auth):
    acme = make_client(client, auth)
    project = new_project(client, auth, acme["id"], hourly_rate="120")
    assert project["effective_rate"] == "120.00"

    r = client.patch(f"/api/projects/{project['id']}", json={"hourly_rate": None}, headers=auth)
    assert r.json()["effective_rate"] == "80.00"


def test_list_projects_filters_by_client(client, auth):
    a = make_client(client, auth, name="Alpha")
    b = make_client(client, auth, name="Beta")
    new_project(client, auth, b["id"], name="Zed")
    new_project(client, auth, a["id"], name="Yak")
    new_project(client, auth, a["id"], name="Ant")

    names = [p["name"] for p in client.get("/api/projects", headers=auth).json()]
    assert names == ["Ant", "Yak", "Zed"]
    only_b = client.get(f"/api/projects?client_id={b['id']}", headers=auth).json()
    assert [p["name"] for p in only_b] == ["Zed"]


def test_cannot_create_project_for_someone_elses_client(client, auth, other_auth):
    theirs = make_client(client, other_auth)
    r = client.post("/api/projects", json={"client_id": theirs["id"], "name": "X"}, headers=auth)
    assert r.status_code == 404


def test_cannot_add_project_to_archived_client(client, auth):
    acme = make_client(client, auth)
    client.post(f"/api/clients/{acme['id']}/archive", headers=auth)
    r = client.post("/api/projects", json={"client_id": acme["id"], "name": "X"}, headers=auth)
    assert r.status_code == 422


def test_project_validation(client, auth):
    acme = make_client(client, auth)
    for payload in (
        {"client_id": acme["id"], "name": ""},
        {"client_id": acme["id"], "name": "X", "color": "red"},
        {"client_id": acme["id"], "name": "X", "hourly_rate": "-5"},
    ):
        assert client.post("/api/projects", json=payload, headers=auth).status_code == 422


def test_archive_and_restore_project(client, auth):
    acme = make_client(client, auth)
    project = new_project(client, auth, acme["id"])
    client.post(f"/api/projects/{project['id']}/archive", headers=auth)
    assert client.get("/api/projects", headers=auth).json() == []
    client.post(f"/api/projects/{project['id']}/restore", headers=auth)
    assert len(client.get("/api/projects", headers=auth).json()) == 1


def test_projects_of_other_users_are_hidden(client, auth, other_auth):
    acme = make_client(client, auth)
    project = new_project(client, auth, acme["id"])
    assert client.get(f"/api/projects/{project['id']}", headers=other_auth).status_code == 404
    assert client.get("/api/projects", headers=other_auth).json() == []


def test_project_budget_and_usage(client, auth):
    acme = make_client(client, auth)
    project = new_project(client, auth, acme["id"], budget_hours="20")
    assert project["budget_hours"] == "20.00"
    assert project["used_seconds"] == 0
    for day in ("05", "06"):
        client.post(
            "/api/entries",
            json={
                "project_id": project["id"],
                "started_at": f"2026-04-{day}T09:00:00Z",
                "ended_at": f"2026-04-{day}T10:30:00Z",
            },
            headers=auth,
        )
    client.post("/api/timer/start", json={"project_id": project["id"]}, headers=auth)
    listed = client.get("/api/projects", headers=auth).json()[0]
    assert listed["used_seconds"] == 10800
    assert (
        client.get(f"/api/projects/{project['id']}", headers=auth).json()["used_seconds"] == 10800
    )

    r = client.patch(f"/api/projects/{project['id']}", json={"budget_hours": None}, headers=auth)
    assert r.json()["budget_hours"] is None
    assert r.json()["used_seconds"] == 10800
    r = client.patch(f"/api/projects/{project['id']}", json={"budget_hours": "0"}, headers=auth)
    assert r.status_code == 422
