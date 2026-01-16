from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GITHUB_TOKENS: str
    TARGET_REPOS: str = "fastapi/fastapi"

    MONGO_URI: str
    MONGO_DB_NAME: str = "github_issues_db"

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "github_issue_classifier"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def tokens_list(self) -> List[str]:
        return [t.strip() for t in self.GITHUB_TOKENS.split(",") if t.strip()]

    @property
    def repos_list(self) -> List[str]:
        return [r.strip() for r in self.TARGET_REPOS.split(",") if r.strip()]


settings = Settings()
