from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from timesheets.db import Base

API_DIR = Path(__file__).resolve().parent.parent


def test_migrations_form_a_single_chain():
    script = ScriptDirectory.from_config(Config(str(API_DIR / "alembic.ini")))
    assert len(script.get_heads()) == 1


def test_migrated_schema_matches_the_models(engine):
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    diff = [d for d in diff if not (d[0] == "remove_table" and d[1].name == "alembic_version")]
    assert diff == []
