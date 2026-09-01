"""
Central settings. Everything that differs between local/dev/prod comes from
env vars so the same image runs everywhere (12-factor style).
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://peblo:peblo@db:5432/peblo"

    # storage: "local" (disk, for dev/CI) or "r2" (Cloudflare R2 / any S3-compatible)
    storage_backend: str = "local"
    storage_local_path: str = "/storage"
    storage_public_base_url: str = "http://localhost:8000/static"

    # only used when storage_backend == "r2"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "peblo-tv"
    r2_public_base_url: str = ""

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    catalogue_key: str = "catalogue"  # logical name; storage adds run-id + extension

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
