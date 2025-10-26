import os

import pytest
from sqlalchemy import text

from timesheets import db
from timesheets.db import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://timesheets:timesheets@localhost:5432/timesheets_test",
)


@pytest.fixture(scope="session")
def engine():
    engine = db.configure(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(request):
    """Empty every table before tests that touch the database."""
    if "engine" not in request.fixturenames and "session" not in request.fixturenames:
        yield
        return
    engine = request.getfixturevalue("engine")
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    if tables:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def session(engine):
    s = db.session_factory()()
    yield s
    s.close()


@pytest.fixture
def client(engine):
    from fastapi.testclient import TestClient

    from timesheets.main import create_app

    with TestClient(create_app()) as c:
        yield c
