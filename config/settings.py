from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    mt5_login: int = 0
    mt5_password: str = ""
    mt5_server: str = "Deriv-Demo"
    mt5_path: Optional[str] = None

    max_daily_loss_pct: float = -3.0
    max_concurrent_positions: int = 6
    default_lot_size: float = 0.01

    jev_api_key: str = ""
    jev_endpoint: str = ""

    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
