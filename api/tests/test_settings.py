def test_defaults(client, auth):
    body = client.get("/api/settings", headers=auth).json()
    assert body["timezone"] == "UTC"
    assert body["rounding"] == "none"
    assert body["currency"] == "EUR"
    assert body["invoice_prefix"] == "INV-"
    assert body["payment_terms_days"] == 14


def test_update_settings(client, auth):
    r = client.patch(
        "/api/settings",
        json={
            "timezone": "Europe/Bucharest",
            "rounding": "15",
            "business_name": "Fran Dev SRL",
            "business_address": "Str. Lunga 1\nBrasov",
            "invoice_prefix": "FD-",
            "payment_terms_days": 30,
        },
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = client.get("/api/settings", headers=auth).json()
    assert body["timezone"] == "Europe/Bucharest"
    assert body["rounding"] == "15"
    assert body["business_address"] == "Str. Lunga 1\nBrasov"
    assert body["payment_terms_days"] == 30


def test_settings_validation(client, auth):
    for payload in (
        {"timezone": "Mars/Base"},
        {"rounding": "10"},
        {"currency": "ZZZ"},
        {"invoice_prefix": "has space"},
        {"payment_terms_days": -1},
    ):
        assert client.patch("/api/settings", json=payload, headers=auth).status_code == 422


def test_weekly_target_hours(client, auth):
    assert client.get("/api/settings", headers=auth).json()["weekly_target_hours"] is None
    r = client.patch("/api/settings", json={"weekly_target_hours": "32.5"}, headers=auth)
    assert r.json()["weekly_target_hours"] == "32.50"
    assert (
        client.patch("/api/settings", json={"weekly_target_hours": "200"}, headers=auth).status_code
        == 422
    )
    r = client.patch("/api/settings", json={"weekly_target_hours": None}, headers=auth)
    assert r.json()["weekly_target_hours"] is None
