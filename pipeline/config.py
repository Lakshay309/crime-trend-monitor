
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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

    # Database
    database_type: str = os.getenv(
        "DATABASE_TYPE", "postgresql"
    ).lower()

    sqlite_path: str = os.getenv(
        "SQLITE_PATH",
        str(PROJECT_ROOT / "data" / "crime_monitor.db")
    )

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
    missing = []

    if not settings.socrata_app_token:
        missing.append("SOCRATA_APP_TOKEN")

    if settings.database_type not in ("sqlite", "postgresql"):
        raise ValueError(
            "DATABASE_TYPE must be sqlite or postgresql."
        )

    if settings.database_type == "postgresql":
        if not settings.db_password:
            missing.append("POSTGRES_PASSWORD")

        if not 1 <= settings.db_port <= 65535:
            raise ValueError("DB_PORT must be between 1 and 65535.")

    if settings.batch_size <= 0:
        raise ValueError("BATCH_SIZE must be greater than zero.")

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )
