def test_unknown_route_has_json_error_body(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "Not Found"}}


def test_validation_errors_list_the_fields(client):
    r = client.post("/api/auth/signup", json={"email": "bad", "password": "x"})
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "validation_failed"
    fields = {d["field"] for d in error["details"]}
    assert {"email", "password", "name"} <= fields


def test_auth_errors_keep_the_www_authenticate_header(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"
    assert r.json()["error"]["code"] == "unauthorized"
