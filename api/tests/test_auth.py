def test_signup_returns_a_token(client):
    r = client.post(
        "/api/auth/signup",
        json={"email": "Ana@Example.com ", "password": "secret-pass", "name": "Ana"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == "ana@example.com"


def test_login_with_correct_password(client):
    client.post(
        "/api/auth/signup",
        json={"email": "ana@example.com", "password": "secret-pass", "name": "A"},
    )
    r = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "secret-pass"})
    assert r.status_code == 200
