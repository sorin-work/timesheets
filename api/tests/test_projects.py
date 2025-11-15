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
