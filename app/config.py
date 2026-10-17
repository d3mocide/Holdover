from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    holdover_token: str = ""
    database_url: str = "sqlite:////data/holdover.db"
    data_dir: str = "/data"
    web_dir: str = "web/dist"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    home_lat: float | None = None
    home_lon: float | None = None
    user_agent: str = "Holdover/0.1 (set USER_AGENT with a contact address)"
    run_scheduler: bool = True

    # Willamette zone on the ODFW stocking schedule (field_zone_value)
    stocking_zone_value: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
