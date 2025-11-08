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
