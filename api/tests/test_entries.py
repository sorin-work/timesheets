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
