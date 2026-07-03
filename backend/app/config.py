"""
Central place for all configuration. Everything is read from environment
variables (see .env.example) so nothing sensitive is hard-coded in git.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- core ---
    APP_NAME: str = "Mother Teresa Transport API"
    ENVIRONMENT: str = "development"

    # --- database ---
    DATABASE_URL: str = "postgresql+psycopg2://mtt_user:mtt_password@localhost:5432/mtt_db"

    # --- auth ---
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours

    # --- CORS ---
    # Comma-separated list of origins allowed to call this API, e.g.
    # "https://mothertheresatransport.com,https://www.mothertheresatransport.com"
    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    # --- email notifications (SMTP) ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@mothertheresatransport.com"
    SMTP_USE_TLS: bool = True

    # --- WhatsApp / SMS notifications (Twilio) ---
    # Leave blank to disable — the app will just log messages instead of sending them,
    # so it runs fine without these during development.
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""  # e.g. "whatsapp:+14155238886"
    TWILIO_SMS_FROM: str = ""       # e.g. "+14155238886"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

CORS_ORIGIN_LIST = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
