from pathlib import Path

import pytest

from ai_act_validator.config import Settings
from ai_act_validator.engine import LegalRulesEngine


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        auth_mode="disabled",
        database_path=tmp_path / "test.db",
    )


@pytest.fixture
def engine(settings: Settings) -> LegalRulesEngine:
    return LegalRulesEngine(
        settings.data_dir / "rules.json",
        settings.data_dir / "obligations.json",
        settings.ruleset_id,
    )
