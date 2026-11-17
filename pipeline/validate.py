import logging

import pandas as pd

logger = logging.getLogger("crime_pipeline.validate")


EXPECTED_COLUMNS = [
    "date_time",
    "id",
    "type",
    "subtype",
    "location",
    "last_updated",
    "description",
]

REQUIRED_COLUMNS = [
    "date_time",
    "id",
    "type",
    "location",
]


def validate_schema(df):
    """Verify that all expected source columns are present."""

    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {sorted(missing_columns)}"
        )

    logger.info("Schema validation successful.")


def validate_id(df):
    """Convert incident IDs to numeric values."""

    df = df.copy()

    original_ids = df["id"].copy()
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    invalid_count = (
        original_ids.notna() & df["id"].isna()
    ).sum()

    if invalid_count:
        logger.warning(
            "Found %s records with invalid incident IDs.",
            invalid_count
        )

    logger.info("Incident ID validation completed.")

    return df


def validate_datetime(df):
    """Parse incident timestamps and identify invalid values."""

    df = df.copy()

    original_dates = df["date_time"].copy()

    df["date_time"] = pd.to_datetime(
        df["date_time"],
        errors="coerce"
    )

    invalid_count = df["date_time"].isna().sum()

    if invalid_count:
        logger.warning(
            "Found %s records with missing or invalid timestamps.",
            invalid_count
        )

    logger.info("Datetime validation completed.")

    return df


def validate_required_fields(df):
    """Report missing values in required columns."""

    for column in REQUIRED_COLUMNS:
        missing_count = df[column].isna().sum()

        if missing_count:
            logger.warning(
                "Column '%s' contains %s missing values.",
                column,
                missing_count
            )

    logger.info("Required-field validation completed.")


def validate_data(df):
    """
    Validate raw incident data before transformation.

    Returns:
        pandas.DataFrame: Validated dataframe with normalized IDs
        and parsed timestamps.
    """

    if df.empty:
        raise ValueError("Extracted dataset is empty.")

    validate_schema(df)

    # Retain only the expected source columns.
    df = df[EXPECTED_COLUMNS].copy()

    df = validate_id(df)
    df = validate_datetime(df)

    validate_required_fields(df)

    logger.info(
        "Validation completed. Records inspected: %s.",
        len(df)
    )

    return df
