import secrets
import json
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="CreatorLab API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")
    storage_root: Path = Field(default=Path("storage"), alias="STORAGE_ROOT")
    database_path: Path = Field(default=Path("storage") / "creatorlab.db", alias="DATABASE_PATH")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    max_upload_mb: int = Field(default=25, alias="MAX_UPLOAD_MB")
    max_batch_upload_mb: int = Field(default=80, alias="MAX_BATCH_UPLOAD_MB")
    max_request_mb: int = Field(default=90, alias="MAX_REQUEST_MB")
    max_image_pixels: int = Field(default=25_000_000, alias="MAX_IMAGE_PIXELS")
    max_pdf_pages: int = Field(default=500, alias="MAX_PDF_PAGES")
    max_pdf_split_outputs: int = Field(default=200, alias="MAX_PDF_SPLIT_OUTPUTS")
    temp_file_ttl_hours: int = Field(default=24, alias="TEMP_FILE_TTL_HOURS")
    output_file_ttl_hours: int = Field(default=168, alias="OUTPUT_FILE_TTL_HOURS")
    worker_threads: int = Field(default=2, alias="WORKER_THREADS")
    worker_queue_size: int = Field(default=128, alias="WORKER_QUEUE_SIZE")
    job_max_retries: int = Field(default=2, alias="JOB_MAX_RETRIES")
    cleanup_interval_seconds: int = Field(default=300, alias="CLEANUP_INTERVAL_SECONDS")
    upload_rate_limit_per_minute: int = Field(default=30, alias="UPLOAD_RATE_LIMIT_PER_MINUTE")
    realesrgan_model_name: str = Field(default="RealESRGAN_x4plus", alias="REALESRGAN_MODEL_NAME")
    realesrgan_weights_url: str = Field(
        default="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        alias="REALESRGAN_WEIGHTS_URL",
    )
    lightweight_ai_model_name: str = Field(default="RealESRGAN_x2plus", alias="LIGHTWEIGHT_AI_MODEL_NAME")
    lightweight_ai_weights_url: str = Field(
        default="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        alias="LIGHTWEIGHT_AI_WEIGHTS_URL",
    )
    enable_heavy_ai: bool = Field(default=False, alias="ENABLE_HEAVY_AI")
    upscale_max_input_pixels: int = Field(default=2_800_000, alias="UPSCALE_MAX_INPUT_PIXELS")
    upscale_max_edge: int = Field(default=2200, alias="UPSCALE_MAX_EDGE")
    upscale_timeout_seconds: int = Field(default=25, alias="UPSCALE_TIMEOUT_SECONDS")
    max_concurrent_ai_jobs: int = Field(default=1, alias="MAX_CONCURRENT_AI_JOBS")
    rembg_model_name: str = Field(default="u2net", alias="REMBG_MODEL_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    auth_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), alias="AUTH_SECRET_KEY")
    session_cookie_name: str = Field(default="creatorlab_session", alias="SESSION_COOKIE_NAME")
    visitor_cookie_name: str = Field(default="creatorlab_visitor", alias="VISITOR_COOKIE_NAME")
    session_ttl_days: int = Field(default=14, alias="SESSION_TTL_DAYS")
    visitor_ttl_days: int = Field(default=180, alias="VISITOR_TTL_DAYS")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_samesite: str = Field(default="lax", alias="SESSION_COOKIE_SAMESITE")
    anonymous_monthly_jobs: int = Field(default=50, alias="ANONYMOUS_MONTHLY_JOBS")
    require_auth_for_jobs: bool = Field(default=False, alias="REQUIRE_AUTH_FOR_JOBS")
    require_email_verification: bool = Field(default=True, alias="REQUIRE_EMAIL_VERIFICATION")
    block_unverified_users_from_jobs: bool = Field(default=False, alias="BLOCK_UNVERIFIED_USERS_FROM_JOBS")
    app_public_url: str = Field(default="http://localhost:3000", alias="APP_PUBLIC_URL")
    api_public_url: str = Field(default="http://localhost:8000", alias="API_PUBLIC_URL")
    mail_backend: str = Field(default="local_file", alias="MAIL_BACKEND")
    mail_from_email: str = Field(default="no-reply@creatorlab.local", alias="MAIL_FROM_EMAIL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    smtp_timeout_seconds: int = Field(default=20, alias="SMTP_TIMEOUT_SECONDS")
    email_verification_ttl_hours: int = Field(default=24, alias="EMAIL_VERIFICATION_TTL_HOURS")
    password_reset_ttl_minutes: int = Field(default=60, alias="PASSWORD_RESET_TTL_MINUTES")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("session_cookie_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value: str):
        normalized = value.strip().lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    @field_validator("max_upload_mb", "max_batch_upload_mb", "max_request_mb", "max_image_pixels", "max_pdf_pages", "max_pdf_split_outputs")
    @classmethod
    def validate_positive_limits(cls, value: int):
        if value <= 0:
            raise ValueError("Configured limits must be positive integers")
        return value


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
