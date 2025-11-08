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
