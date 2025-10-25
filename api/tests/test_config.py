from timesheets.config import Settings


def test_settings_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")
    monkeypatch.setenv("TOKEN_TTL_MINUTES", "30")
    settings = Settings()
    assert settings.database_url.endswith("@db:5432/x")
    assert settings.token_ttl_minutes == 30
