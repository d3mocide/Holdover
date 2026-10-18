from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

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
    # Accounts. cookie_secure=None means "Secure when the request arrived over HTTPS" (directly or via the
    # reverse proxy's X-Forwarded-Proto); set true/false to force it.
    cookie_secure: bool | None = None
    session_days: int = 90
    invite_days: int = 7

    # Scoring weights (tunable starting points, not validated). Missing-data factors are dropped
    # and the remaining weights renormalised, see app/scoring.py.
    w_stocking: float = 0.30
    w_report: float = 0.25
    w_flow: float = 0.20
    w_forecast: float = 0.15
    w_distance: float = 0.10

    # Willamette zone on the ODFW stocking schedule (field_zone_value)
    stocking_zone_value: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
