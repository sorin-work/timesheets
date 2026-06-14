from fastapi.testclient import TestClient

from timesheets.main import create_app


def test_health_reports_the_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_fails_without_a_database(engine, monkeypatch):
    from sqlalchemy import create_engine

    from timesheets import db

    broken = create_engine("postgresql+psycopg://nobody:nothing@127.0.0.1:1/none")
    monkeypatch.setattr(db, "get_engine", lambda: broken)
    response = TestClient(create_app()).get("/api/health")
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


def test_cors_allows_the_dev_frontend():
    client = TestClient(create_app())
    r = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
