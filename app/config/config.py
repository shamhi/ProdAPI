import os
import pathlib
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVER_ADDRESS: str = "0.0.0.0:8080"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8080

    POSTGRES_CONN: str = os.environ.get('POSTGRES_CONN')
    POSTGRES_JDBC_URL: Any = os.environ.get('POSTGRES_JDBC_URL')
    POSTGRES_USER: str = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD: str = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_HOST: str = os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT: int = os.environ.get('POSTGRES_PORT')
    POSTGRES_DATABASE: str = os.environ.get('POSTGRES_DATABASE')

    RANDOM_SECRET: str = os.environ.get('RANDOM_SECRET')
    ALGORITHM: str = os.environ.get('ALGORITHM')

    ACCESS_TOKEN_EXPIRES_MINUTES: int = os.environ.get('ACCESS_TOKEN_EXPIRES_MINUTES')
    ACCESS_TOKEN_EXPIRES_HOURS: int = os.environ.get('ACCESS_TOKEN_EXPIRES_HOURS')
    ACCESS_TOKEN_EXPIRES_DAYS: int = os.environ.get('ACCESS_TOKEN_EXPIRES_DAYS')

    class Config:
        env_nested_delimiter = '__'
        env_file = f"{pathlib.Path(__file__).resolve().parent.parent.parent}/.env"


Config = Settings()
