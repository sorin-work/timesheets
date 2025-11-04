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
