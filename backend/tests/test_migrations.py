"""Unit tests for Alembic migration configuration and revision integrity."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_configuration_and_head_revision() -> None:
    """Verify Alembic finds initial migration revision matching schema models."""
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    assert ini_path.exists(), f"Alembic configuration file not found at {ini_path}"

    alembic_cfg = Config(str(ini_path))
    script = ScriptDirectory.from_config(alembic_cfg)

    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "0002_ingestion_pipeline"

    for rev_id in ("0001_initial_schema", "0002_ingestion_pipeline"):
        revision = script.get_revision(rev_id)
        assert revision is not None
        assert revision.module is not None
        assert hasattr(revision.module, "upgrade")
        assert hasattr(revision.module, "downgrade")
