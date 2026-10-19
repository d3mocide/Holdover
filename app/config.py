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
    # The weekly report extraction can use a different (slower, stronger) model and a long timeout: it runs once a week, in the
    # background. Empty means the same model as everything else.
    llm_extract_model: str = ""
    llm_extract_timeout: float = 1800
    llm_timeout: float = 180  # seconds per request; a reasoning model can take several minutes on a long report
    home_lat: float | None = None
    home_lon: float | None = None
    user_agent: str = "Holdover/0.1 (set USER_AGENT with a contact address)"
    run_scheduler: bool = True
    # USGS: "ogc" = the Water Data API (api.waterdata.usgs.gov). "legacy" = waterservices.usgs.gov, which USGS is
    # retiring in early 2027; kept only as a fallback until then and to be deleted afterwards.
    usgs_api: str = "ogc"
    # Accounts. cookie_secure=None means "Secure when the request arrived over HTTPS" (directly or via the
    # reverse proxy's X-Forwarded-Proto); set true/false to force it.
    cookie_secure: bool | None = None
    session_days: int = 90
    # Reverse proxies in front of the app that append to X-Forwarded-For (0 = trust nothing and use the socket address).
    # The login throttle uses the address this yields, so with a proxy and 0 hops everyone shares one address.
    trusted_proxy_hops: int = 0
    invite_days: int = 7

    # Scoring weights (tunable starting points, not validated). Missing-data factors are dropped
    # and the remaining weights renormalised, see app/scoring.py.
    w_stocking: float = 0.30
    w_report: float = 0.25
    w_flow: float = 0.20
    w_forecast: float = 0.15
    w_distance: float = 0.10

    # Willamette zone on the ODFW stocking schedule (field_zone_value); the default for a single-zone fetch
    stocking_zone_value: int = 6
    # Zones the scheduled stocking job fetches and the app offers (keys from app/zones). Each zone is a few pages a day.
    enabled_zones: str = "willamette,central,northwest"


@lru_cache
def get_settings() -> Settings:
    return Settings()
