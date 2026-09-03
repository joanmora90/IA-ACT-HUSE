from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Act Validator"
    app_env: Literal["development", "test", "production"] = "development"
    auth_mode: Literal["disabled", "entra"] = "disabled"
    database_path: Path = Path("data/ai_act_validator.db")
    ruleset_id: str = "EU_AI_ACT_2026_07_27_V0_1"
    rule_source: Literal["bundle", "dataverse"] = "bundle"
    entra_tenant_id: str | None = None
    entra_audience: str | None = None
    dataverse_url: str | None = None
    dataverse_tenant_id: str | None = None
    dataverse_client_id: str | None = None
    dataverse_client_secret: str | None = None
    dataverse_rules_entity_set: str = "aia_rules"
    dataverse_questions_entity_set: str = "aia_questions"
    dataverse_obligations_entity_set: str = "aia_obligations"

    @property
    def data_dir(self) -> Path:
        return Path(__file__).parent / "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
