from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

API_DIR = Path(__file__).resolve().parent.parent


def test_migrations_form_a_single_chain():
    script = ScriptDirectory.from_config(Config(str(API_DIR / "alembic.ini")))
    assert len(script.get_heads()) == 1
