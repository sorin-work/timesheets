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
        return [
            e["description"]
            for e in client.get(f"/api/entries?{query}", headers=auth).json()["items"]
        ]

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


def test_entries_are_paginated(client, auth, project):
    for day in range(1, 5):
        client.post(
            "/api/entries",
            json=entry(
                project["id"], start=f"2025-11-0{day}T09:00:00Z", end=f"2025-11-0{day}T10:00:00Z"
            ),
            headers=auth,
        )
    first = client.get("/api/entries?page_size=2", headers=auth).json()
    assert first["total"] == 4
    assert first["pages"] == 2
    assert [e["started_at"][:10] for e in first["items"]] == ["2025-11-04", "2025-11-03"]
    second = client.get("/api/entries?page_size=2&page=2", headers=auth).json()
    assert [e["started_at"][:10] for e in second["items"]] == ["2025-11-02", "2025-11-01"]


def test_empty_entries_list_has_one_page(client, auth):
    body = client.get("/api/entries", headers=auth).json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 50, "pages": 1}
