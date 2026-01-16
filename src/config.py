from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GitHub Configuration
    GITHUB_TOKEN: SecretStr
    GITHUB_REPOSITORY: str = "fastapi/fastapi"

    # Database Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "github_data"

    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "default_experiment"

    # Configuration Pydantic
    # Lit automatiquement le fichier .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore les variables inutiles du .env
    )


# On instancie la config une seule fois pour l'importer partout
settings = Settings()
