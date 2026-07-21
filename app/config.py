from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    dry_run: bool = True
    timezone: str = "America/New_York"

    gracefinance_api_url: str = "https://gracefinance.co"
    gracefinance_index_path: str = "/index/raw-ohlc?range=1D"
    gracefinance_site_url: str = "https://gracefinance.co"

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    x_bearer_token: str = ""
    auto_approve_replies: bool = False
    engagement_interval_minutes: int = 60

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""
    reddit_user_agent: str = "GraceFinanceGrowth/1.0"
    reddit_subreddit: str = ""

    linkedin_access_token: str = ""
    linkedin_author_urn: str = ""
    linkedin_version: str = "202606"

    morning_post_hour: int = 8
    evening_post_hour: int = 18
    weekly_post_day: str = "mon"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def x_ready(self) -> bool:
        return all(
            [
                self.x_api_key,
                self.x_api_secret,
                self.x_access_token,
                self.x_access_token_secret,
            ]
        )

    @property
    def reddit_ready(self) -> bool:
        return all(
            [
                self.reddit_client_id,
                self.reddit_client_secret,
                self.reddit_username,
                self.reddit_password,
                self.reddit_subreddit,
            ]
        )

    @property
    def linkedin_ready(self) -> bool:
        return bool(self.linkedin_access_token and self.linkedin_author_urn)


@lru_cache
def get_settings() -> Settings:
    return Settings()
