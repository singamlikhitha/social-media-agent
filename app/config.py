from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Instagram
    INSTAGRAM_ACCESS_TOKEN: str | None = None
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str | None = None

    # YouTube
    YOUTUBE_CLIENT_SECRETS_FILE: str | None = None
    YOUTUBE_OAUTH_TOKEN_FILE: str = "youtube_token.json"

    # Database
    DATABASE_URL: str = "sqlite:///./social_media_agent.db"

    # Scheduler
    TIMEZONE: str = "UTC"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def instagram_configured(self) -> bool:
        return bool(self.INSTAGRAM_ACCESS_TOKEN and self.INSTAGRAM_BUSINESS_ACCOUNT_ID)

    @property
    def youtube_configured(self) -> bool:
        return bool(self.YOUTUBE_CLIENT_SECRETS_FILE)


settings = Settings()
