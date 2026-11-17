import logging
import sys

from pipeline.config import settings


def configure_logging():
    """Configure consistent application-wide logging."""

    logging.basicConfig(
        level=getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO
        ),
        format=(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

    return logging.getLogger("crime_pipeline")


logger = configure_logging()
