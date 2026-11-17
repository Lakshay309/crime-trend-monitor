import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Socrata API
    socrata_domain: str = os.getenv(
        "SOCRATA_DOMAIN", "data.cambridgema.gov"
    )
    socrata_dataset_id: str = os.getenv(
        "SOCRATA_DATASET_ID", "3gki-wyrb"
    )
    socrata_app_token: str = os.getenv(
        "SOCRATA_APP_TOKEN", ""
    )

    # PostgreSQL
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5433"))
    db_name: str = os.getenv("POSTGRES_DB", "cpd_db")
    db_user: str = os.getenv("POSTGRES_USER", "crime_admin")
    db_password: str = os.getenv("POSTGRES_PASSWORD", "")

    # Pipeline
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    batch_size: int = int(os.getenv("BATCH_SIZE", "5000"))


settings = Settings()


def validate_settings():
    """Validate configuration required to run the pipeline."""

    missing = []

    if not settings.socrata_app_token:
        missing.append("SOCRATA_APP_TOKEN")

    if not settings.db_password:
        missing.append("POSTGRES_PASSWORD")

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )

    if not 1 <= settings.db_port <= 65535:
        raise ValueError("DB_PORT must be between 1 and 65535.")

    if settings.batch_size <= 0:
        raise ValueError("BATCH_SIZE must be greater than zero.")
