def test_create_and_list_clients(client, auth):
    r = client.post(
        "/api/clients",
        json={"name": "  Acme Ltd ", "currency": "usd", "hourly_rate": "85.50"},
        headers=auth,
    )
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "Acme Ltd"
    assert created["currency"] == "USD"
    assert created["hourly_rate"] == "85.50"

    listed = client.get("/api/clients", headers=auth).json()
    assert [c["name"] for c in listed] == ["Acme Ltd"]


def test_archived_clients_are_hidden_by_default(client, auth):
    cid = client.post("/api/clients", json={"name": "Old Co"}, headers=auth).json()["id"]
    client.post("/api/clients", json={"name": "New Co"}, headers=auth)

    r = client.post(f"/api/clients/{cid}/archive", headers=auth)
    assert r.status_code == 200
    assert r.json()["archived_at"] is not None

    names = [c["name"] for c in client.get("/api/clients", headers=auth).json()]
    assert names == ["New Co"]
    everything = client.get("/api/clients?include_archived=true", headers=auth).json()
    assert len(everything) == 2

    client.post(f"/api/clients/{cid}/restore", headers=auth)
    assert len(client.get("/api/clients", headers=auth).json()) == 2


def test_client_validation(client, auth):
    bad = [
        {"name": ""},
        {"name": "   "},
        {"name": "X", "currency": "XYZ"},
        {"name": "X", "hourly_rate": "-1"},
        {"name": "X", "hourly_rate": "12.345"},
        {"name": "X", "email": "nope"},
    ]
    for payload in bad:
        r = client.post("/api/clients", json=payload, headers=auth)
        assert r.status_code == 422, payload


def test_update_client_partially(client, auth):
    cid = client.post(
        "/api/clients", json={"name": "Acme", "hourly_rate": "50"}, headers=auth
    ).json()["id"]
    r = client.patch(
        f"/api/clients/{cid}", json={"hourly_rate": "65.00", "notes": "  "}, headers=auth
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Acme"
    assert body["hourly_rate"] == "65.00"
    assert body["notes"] is None


def test_clients_of_other_users_are_not_visible(client, auth, other_auth):
    cid = client.post("/api/clients", json={"name": "Mine"}, headers=auth).json()["id"]
    assert client.get("/api/clients", headers=other_auth).json() == []
    assert client.get(f"/api/clients/{cid}", headers=other_auth).status_code == 404
    assert (
        client.patch(f"/api/clients/{cid}", json={"name": "x"}, headers=other_auth).status_code
        == 404
    )
    assert client.delete(f"/api/clients/{cid}", headers=other_auth).status_code == 404
    assert client.get(f"/api/clients/{cid}", headers=auth).status_code == 200


def test_delete_client(client, auth):
    cid = client.post("/api/clients", json={"name": "Temp"}, headers=auth).json()["id"]
    assert client.delete(f"/api/clients/{cid}", headers=auth).status_code == 204
    assert client.get(f"/api/clients/{cid}", headers=auth).status_code == 404


def test_clients_require_auth(client):
    assert client.get("/api/clients").status_code == 401


def test_clients_with_invoices_cannot_be_deleted(client, auth, project):
    client.post(
        "/api/entries",
        json={
            "project_id": project["id"],
            "started_at": "2026-05-04T09:00:00Z",
            "ended_at": "2026-05-04T10:00:00Z",
        },
        headers=auth,
    )
    client.post(
        "/api/invoices/generate",
        json={
            "client_id": project["client_id"],
            "period_start": "2026-05-01",
            "period_end": "2026-05-31",
        },
        headers=auth,
    )
    r = client.delete(f"/api/clients/{project['client_id']}", headers=auth)
    assert r.status_code == 409
    assert "archive" in r.json()["error"]["message"]


def test_search_clients_by_name_or_email(client, auth):
    for name, email in (
        ("Ärzte Praxis", "info@praxis.example"),
        ("bolt", None),
        ("Acme", "a@acme.example"),
    ):
        client.post("/api/clients", json={"name": name, "email": email}, headers=auth)

    def names(q):
        return [c["name"] for c in client.get("/api/clients", params={"q": q}, headers=auth).json()]

    assert names("") == ["Acme", "bolt", "Ärzte Praxis"]
    assert names("ÄRZTE") == ["Ärzte Praxis"]
    assert names("acme.example") == ["Acme"]
    assert names("zzz") == []


def test_client_summary(client, auth, project):
    def log(start, end, billable=True):
        client.post(
            "/api/entries",
            json={
                "project_id": project["id"],
                "started_at": start,
                "ended_at": end,
                "billable": billable,
            },
            headers=auth,
        )

    log("2026-05-04T09:00:00Z", "2026-05-04T11:00:00Z")
    log("2026-05-05T09:00:00Z", "2026-05-05T09:30:00Z", billable=False)
    inv = client.post(
        "/api/invoices/generate",
        json={
            "client_id": project["client_id"],
            "period_start": "2026-05-01",
            "period_end": "2026-05-31",
        },
        headers=auth,
    ).json()
    client.post(f"/api/invoices/{inv['id']}/send", headers=auth)
    log("2026-06-01T09:00:00Z", "2026-06-01T10:00:00Z")

    summary = client.get(f"/api/clients/{project['client_id']}/summary", headers=auth).json()
    assert summary["projects"] == 1
    assert summary["tracked_seconds"] == 3.5 * 3600
    assert summary["unbilled_seconds"] == 3600
    assert summary["last_tracked_at"].startswith("2026-06-01T09:00")
    assert summary["invoiced"] == "200.00"
    assert summary["outstanding"] == "200.00"
    assert summary["paid"] == "0.00"
