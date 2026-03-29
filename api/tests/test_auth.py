from datetime import UTC, datetime, timedelta

import jwt

from timesheets.config import get_settings


def signup(client, email="ana@example.com", password="secret-pass", name="Ana"):
    return client.post(
        "/api/auth/signup", json={"email": email, "password": password, "name": name}
    )


def test_signup_returns_a_token(client):
    r = signup(client, email="Ana@Example.com ")
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "ana@example.com"
    assert "password_hash" not in body["user"]


def test_signup_rejects_duplicate_email_case_insensitively(client):
    signup(client)
    r = signup(client, email="ANA@example.com")
    assert r.status_code == 409


def test_signup_validates_input(client):
    assert signup(client, password="short").status_code == 422
    assert signup(client, email="not-an-email").status_code == 422
    assert signup(client, name="   ").status_code == 422


def test_login_with_correct_password(client):
    signup(client)
    r = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "secret-pass"})
    assert r.status_code == 200
    assert r.json()["user"]["name"] == "Ana"


def test_login_with_wrong_password_or_unknown_email(client):
    signup(client)
    r = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "nope-nope"})
    assert r.status_code == 401
    r = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret-pass"})
    assert r.status_code == 401


def test_me_requires_a_token(client):
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_me_returns_the_current_user(client, auth):
    r = client.get("/api/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["email"] == "freelancer@example.com"


def test_expired_token_is_rejected(client, auth):
    me = client.get("/api/auth/me", headers=auth).json()
    past = datetime.now(UTC) - timedelta(days=1)
    token = jwt.encode(
        {"sub": str(me["id"]), "iat": past, "exp": past + timedelta(minutes=5)},
        get_settings().secret_key,
        algorithm="HS256",
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_change_password(client, auth):
    r = client.post(
        "/api/auth/password",
        json={"current_password": "password123", "new_password": "a-new-secret"},
        headers=auth,
    )
    assert r.status_code == 204
    login = {"email": "freelancer@example.com"}
    assert (
        client.post("/api/auth/login", json={**login, "password": "password123"}).status_code == 401
    )
    assert (
        client.post("/api/auth/login", json={**login, "password": "a-new-secret"}).status_code
        == 200
    )


def test_change_password_checks_the_current_one(client, auth):
    r = client.post(
        "/api/auth/password",
        json={"current_password": "wrong-one", "new_password": "a-new-secret"},
        headers=auth,
    )
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "current_password"
    r = client.post(
        "/api/auth/password",
        json={"current_password": "password123", "new_password": "short"},
        headers=auth,
    )
    assert r.status_code == 422
