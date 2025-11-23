def entry(project_id, start="2025-11-17T09:00:00Z", end="2025-11-17T10:30:00Z", **kw):
    return {"project_id": project_id, "started_at": start, "ended_at": end, **kw}


def test_create_manual_entry(client, auth, project):
    r = client.post(
        "/api/entries", json=entry(project["id"], description=" Homepage "), headers=auth
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["duration_seconds"] == 5400
    assert body["description"] == "Homepage"
    assert body["billable"] is True
    assert body["source"] == "manual"
    assert body["client_name"] == "Acme"
    assert body["hourly_rate"] == "100.00"


def test_filter_entries(client, auth, project):
    other = client.post(
        "/api/projects", json={"client_id": project["client_id"], "name": "Ops"}, headers=auth
    ).json()
    client.post("/api/entries", json=entry(project["id"], description="design"), headers=auth)
    client.post(
        "/api/entries",
        json=entry(
            other["id"],
            start="2025-11-18T09:00:00Z",
            end="2025-11-18T09:30:00Z",
            billable=False,
            description="server patching",
        ),
        headers=auth,
    )

    def ids(query):
        return [e["description"] for e in client.get(f"/api/entries?{query}", headers=auth).json()]

    assert ids("") == ["server patching", "design"]
    assert ids(f"project_id={other['id']}") == ["server patching"]
    assert ids("billable=true") == ["design"]
    assert ids("from=2025-11-18") == ["server patching"]
    assert ids("to=2025-11-17") == ["design"]
    assert ids("q=PATCH") == ["server patching"]
    assert ids(f"client_id={project['client_id']}&from=2025-11-17&to=2025-11-18") == [
        "server patching",
        "design",
    ]
