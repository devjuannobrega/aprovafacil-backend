from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Aprova Fácil API"
    APP_VERSION: str = "DEV-1.0.2"
    DEBUG: bool = False

    DATABASE_URL: str

    MP_PUBLIC_KEY: str
    MP_ACCESS_TOKEN: str

    API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
