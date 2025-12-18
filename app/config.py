from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Alpha Vantage
    ALPHA_VANTAGE_API_KEY: str

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Trading
    DEFAULT_BALANCE: float = 100000.00
    STOCK_TRANSACTION_FEE: float = 0.0
    CRYPTO_TRANSACTION_FEE: float = 0.0
    FOREX_TRANSACTION_FEE: float = 0.0

    class Config:
        env_file = ".env"


settings = Settings()
