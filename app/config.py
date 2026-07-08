from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/social_media_agent"

    # JWT Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Token Encryption
    TOKEN_ENCRYPTION_KEY: str = ""  # 32-byte base64-encoded key for AES-256-GCM

    # OAuth - Meta (Instagram + Facebook)
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_REDIRECT_URI: str = "http://localhost:3000/oauth/meta/callback"

    # OAuth - Google (YouTube)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/oauth/google/callback"

    # OAuth - Twitter/X
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://localhost:3000/oauth/twitter/callback"

    # OAuth - LinkedIn
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:3000/oauth/linkedin/callback"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Scheduler
    TIMEZONE: str = "UTC"

    # Together AI (free image generation)
    TOGETHER_API_KEY: str = ""

    # Replicate (AI video generation)
    REPLICATE_API_TOKEN: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"  # "text" for local dev, "json" for structured logs (Cloud Run)

    # Telemetry (OpenTelemetry / OTLP)
    ENVIRONMENT: str = "development"  # dev / staging / production — becomes deployment.environment
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "social-media-backend"
    # Exporter backend: "otlp" (vendor-neutral collector) or "gcp" (Google Cloud
    # Trace + Cloud Monitoring directly, via Application Default Credentials).
    OTEL_EXPORTER_TYPE: str = "otlp"
    # GCP project for the gcp exporter; blank = auto-detect from ADC / metadata server.
    GOOGLE_CLOUD_PROJECT: str = ""
    # OTLP collector endpoint, e.g. "http://localhost:4318" (http) or "localhost:4317" (grpc).
    # Leave blank to use the SDK default for the selected protocol. (otlp mode only)
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_PROTOCOL: str = "http/protobuf"  # "http/protobuf" or "grpc"
    # Comma-separated header list, e.g. "authorization=Bearer xxx,x-tenant=abc"
    OTEL_EXPORTER_OTLP_HEADERS: str = ""
    OTEL_TRACES_SAMPLER_RATIO: float = 1.0  # 0.0–1.0 (parent-based ratio sampler)
    OTEL_EXPORT_METRICS: bool = True  # export metrics (Cloud Monitoring in gcp mode)
    OTEL_EXPORT_LOGS: bool = True  # ship logs via OTLP (ignored in gcp mode — uses stdout)

    # Plan Limits
    FREE_PLAN_MAX_ACCOUNTS: int = 2
    FREE_PLAN_MAX_POSTS_PER_MONTH: int = 10
    PRO_PLAN_MAX_ACCOUNTS: int = 10
    PRO_PLAN_MAX_POSTS_PER_MONTH: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def meta_configured(self) -> bool:
        return bool(self.META_APP_ID and self.META_APP_SECRET)

    @property
    def google_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def twitter_configured(self) -> bool:
        return bool(self.TWITTER_CLIENT_ID and self.TWITTER_CLIENT_SECRET)

    @property
    def linkedin_configured(self) -> bool:
        return bool(self.LINKEDIN_CLIENT_ID and self.LINKEDIN_CLIENT_SECRET)


settings = Settings()
