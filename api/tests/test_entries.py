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
    assert body == {
        "items": [],
        "total": 0,
        "total_seconds": 0,
        "page": 1,
        "page_size": 50,
        "pages": 1,
    }


def test_entry_validation(client, auth, project):
    pid = project["id"]
    bad = [
        entry(pid, end="2025-11-17T09:00:00Z"),  # zero length
        entry(pid, end="2025-11-17T08:00:00Z"),  # ends before it starts
        entry(pid, end="2025-11-18T09:00:01Z"),  # longer than a day
        entry(pid, start="2025-11-17T09:00:00", end="2025-11-17T10:00:00"),  # no timezone
        entry(pid, description="x" * 501),
    ]
    for payload in bad:
        r = client.post("/api/entries", json=payload, headers=auth)
        assert r.status_code == 422, payload


def test_entry_billable_defaults_to_project_setting(client, auth, project):
    client.patch(f"/api/projects/{project['id']}", json={"billable": False}, headers=auth)
    r = client.post("/api/entries", json=entry(project["id"]), headers=auth)
    assert r.json()["billable"] is False
    r = client.post("/api/entries", json=entry(project["id"], billable=True), headers=auth)
    assert r.json()["billable"] is True


def test_update_entry(client, auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    r = client.patch(
        f"/api/entries/{eid}",
        json={
            "started_at": "2025-11-17T08:00:00Z",
            "ended_at": "2025-11-17T08:45:00Z",
            "description": "standup",
        },
        headers=auth,
    )
    assert r.status_code == 200
    assert r.json()["duration_seconds"] == 2700
    assert r.json()["description"] == "standup"


def test_cannot_log_time_on_archived_project(client, auth, project):
    client.post(f"/api/projects/{project['id']}/archive", headers=auth)
    r = client.post("/api/entries", json=entry(project["id"]), headers=auth)
    assert r.status_code == 422


def test_entries_are_private(client, auth, other_auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    assert client.get(f"/api/entries/{eid}", headers=other_auth).status_code == 404
    assert client.delete(f"/api/entries/{eid}", headers=other_auth).status_code == 404
    assert client.get("/api/entries", headers=other_auth).json()["total"] == 0
    r = client.post("/api/entries", json=entry(project["id"]), headers=other_auth)
    assert r.status_code == 404


def test_delete_entry(client, auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    assert client.delete(f"/api/entries/{eid}", headers=auth).status_code == 204
    assert client.get(f"/api/entries/{eid}", headers=auth).status_code == 404


def test_last_partial_page_is_counted(client, auth, project):
    for day in range(1, 6):
        client.post(
            "/api/entries",
            json=entry(
                project["id"], start=f"2025-11-0{day}T09:00:00Z", end=f"2025-11-0{day}T10:00:00Z"
            ),
            headers=auth,
        )
    body = client.get("/api/entries?page_size=2", headers=auth).json()
    assert body["total"] == 5
    assert body["pages"] == 3
    last = client.get("/api/entries?page_size=2&page=3", headers=auth).json()
    assert [e["started_at"][:10] for e in last["items"]] == ["2025-11-01"]


def test_export_entries_as_csv(client, auth, project):
    client.post(
        "/api/entries", json=entry(project["id"], description='Fix "quotes", commas'), headers=auth
    )
    client.post(
        "/api/entries",
        json=entry(project["id"], start="2025-11-18T09:00:00Z", end="2025-11-18T09:15:00Z"),
        headers=auth,
    )
    r = client.get("/api/entries/export.csv?from=2025-11-17&to=2025-11-17", headers=auth)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0].startswith("date,start,end,client")
    assert lines[1] == '2025-11-17,09:00,10:30,Acme,Website,"Fix ""quotes"", commas",1.50,yes,no'
    assert len(lines) == 2


def test_bulk_mark_non_billable_and_delete(client, auth, other_auth, project):
    ids = [
        client.post(
            "/api/entries",
            json=entry(
                project["id"], start=f"2025-11-0{d}T09:00:00Z", end=f"2025-11-0{d}T10:00:00Z"
            ),
            headers=auth,
        ).json()["id"]
        for d in (1, 2, 3)
    ]
    r = client.post(
        "/api/entries/bulk", json={"ids": ids[:2], "action": "non_billable"}, headers=auth
    )
    assert r.json() == {"updated": 2, "deleted": 0}
    flags = {
        e["id"]: e["billable"] for e in client.get("/api/entries", headers=auth).json()["items"]
    }
    assert flags == {ids[0]: False, ids[1]: False, ids[2]: True}

    r = client.post("/api/entries/bulk", json={"ids": ids, "action": "delete"}, headers=other_auth)
    assert r.status_code == 404
    r = client.post("/api/entries/bulk", json={"ids": [ids[2]], "action": "delete"}, headers=auth)
    assert r.json() == {"updated": 0, "deleted": 1}
    assert client.get("/api/entries", headers=auth).json()["total"] == 2


def test_bulk_refuses_invoiced_entries(client, auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    client.post(
        "/api/invoices/generate",
        json={
            "client_id": project["client_id"],
            "period_start": "2025-11-01",
            "period_end": "2025-11-30",
        },
        headers=auth,
    )
    r = client.post("/api/entries/bulk", json={"ids": [eid], "action": "delete"}, headers=auth)
    assert r.status_code == 409
    assert (
        client.post(
            "/api/entries/bulk", json={"ids": [], "action": "delete"}, headers=auth
        ).status_code
        == 422
    )


def test_update_cannot_move_the_end_before_the_start(client, auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    r = client.patch(f"/api/entries/{eid}", json={"ended_at": "2025-11-17T08:00:00Z"}, headers=auth)
    assert r.status_code == 422
    r = client.patch(
        f"/api/entries/{eid}", json={"started_at": "2025-11-17T11:00:00Z"}, headers=auth
    )
    assert r.status_code == 422
    r = client.patch(f"/api/entries/{eid}", json={"ended_at": "2025-11-18T10:00:00Z"}, headers=auth)
    assert r.status_code == 422
    assert client.get(f"/api/entries/{eid}", headers=auth).json()["duration_seconds"] == 5400


def test_update_only_the_end_time(client, auth, project):
    eid = client.post("/api/entries", json=entry(project["id"]), headers=auth).json()["id"]
    r = client.patch(f"/api/entries/{eid}", json={"ended_at": "2025-11-17T09:45:00Z"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["duration_seconds"] == 2700


def test_list_reports_the_total_duration_of_all_matches(client, auth, project):
    for day in (1, 2, 3):
        client.post(
            "/api/entries",
            json=entry(
                project["id"], start=f"2025-11-0{day}T09:00:00Z", end=f"2025-11-0{day}T09:20:00Z"
            ),
            headers=auth,
        )
    body = client.get("/api/entries?page_size=1", headers=auth).json()
    assert len(body["items"]) == 1
    assert body["total_seconds"] == 3600
