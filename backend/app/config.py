from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PrivacyOps Africa Core API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/privacyops"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 20

    github_api_base: str = "https://api.github.com"
    gitlab_api_base: str = "https://gitlab.com/api/v4"

    oauth_google_client_id: str | None = None
    oauth_google_client_secret: str | None = None
    oauth_google_authorize_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    oauth_google_token_url: str = "https://oauth2.googleapis.com/token"
    oauth_google_userinfo_url: str = "https://openidconnect.googleapis.com/v1/userinfo"
    oauth_google_scopes: str = "openid email profile"
    oauth_google_redirect_uri: str | None = None

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_starter: str | None = None
    stripe_price_growth: str | None = None
    stripe_price_enterprise: str | None = None

    aws_region: str = "us-east-1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
