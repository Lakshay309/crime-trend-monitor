import logging
import time

import pandas as pd
from sodapy import Socrata

from pipeline.config import settings

logger = logging.getLogger("crime_pipeline.extract")


def extract_data():
    """
    Extract all available Cambridge Police incident records
    from the Socrata Open Data API.

    Returns:
        pandas.DataFrame: Raw incident records.
    """

    if not settings.socrata_app_token:
        raise ValueError("SOCRATA_APP_TOKEN is not configured.")

    client = Socrata(
        settings.socrata_domain,
        settings.socrata_app_token,
        timeout=60
    )

    records = []
    offset = 0
    limit = settings.batch_size

    try:
        logger.info("Starting Socrata data extraction.")

        while True:
            for attempt in range(1, 4):
                try:
                    batch = client.get(
                        settings.socrata_dataset_id,
                        limit=limit,
                        offset=offset
                    )
                    break

                except Exception:
                    logger.exception(
                        "API request failed. Attempt %s of 3.",
                        attempt
                    )

                    if attempt == 3:
                        raise

                    time.sleep(2 ** attempt)

            if not batch:
                break

            records.extend(batch)

            logger.info(
                "Retrieved %s records. Total: %s.",
                len(batch),
                len(records)
            )

            offset += len(batch)

            if len(batch) < limit:
                break

        dataframe = pd.DataFrame.from_records(records)

        logger.info(
            "Extraction completed. Total records: %s.",
            len(dataframe)
        )

        return dataframe

    finally:
        client.close()
        logger.info("Socrata API connection closed.")
