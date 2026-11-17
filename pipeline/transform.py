import logging

import pandas as pd

logger = logging.getLogger("crime_pipeline.transform")


REQUIRED_COLUMNS = [
    "date_time",
    "id",
    "type",
    "location",
]


def remove_invalid_rows(df):
    """Remove records missing essential information."""

    initial_count = len(df)

    df = df.dropna(subset=REQUIRED_COLUMNS).copy()

    removed_count = initial_count - len(df)

    logger.info(
        "Removed %s records with missing required values.",
        removed_count
    )

    return df


def remove_duplicates(df):
    """Keep only one record per incident ID."""

    initial_count = len(df)

    df = df.drop_duplicates(
        subset=["id"],
        keep="last"
    ).copy()

    removed_count = initial_count - len(df)

    logger.info(
        "Removed %s duplicate incident records.",
        removed_count
    )

    return df


def normalize_data_types(df):
    """Convert fields to database-compatible data types."""

    df = df.copy()

    df["id"] = df["id"].astype("int64")

    df["date_time"] = pd.to_datetime(
        df["date_time"],
        errors="coerce"
    )

    df["last_updated"] = pd.to_datetime(
        df["last_updated"],
        errors="coerce"
    )

    return df


def create_datetime_features(df):
    """Extract analytical time features."""

    df = df.copy()

    df["year"] = df["date_time"].dt.year.astype("int64")
    df["month"] = df["date_time"].dt.month.astype("int64")
    df["day"] = df["date_time"].dt.day.astype("int64")
    df["hour"] = df["date_time"].dt.hour.astype("int64")
    df["minute"] = df["date_time"].dt.minute.astype("int64")
    df["second"] = df["date_time"].dt.second.astype("int64")

    df["day_of_week"] = df["date_time"].dt.day_name()

    return df


def transform_data(df):
    """
    Clean incident records and generate analytical features.

    Returns:
        pandas.DataFrame: Cleaned and transformed records.
    """

    if df.empty:
        raise ValueError("Cannot transform an empty dataset.")

    initial_count = len(df)

    logger.info(
        "Starting transformation of %s records.",
        initial_count
    )

    df = remove_invalid_rows(df)
    df = remove_duplicates(df)
    df = normalize_data_types(df)

    # Remove any timestamps that could not be parsed.
    df = df.dropna(subset=["date_time"]).copy()

    df = create_datetime_features(df)

    logger.info(
        "Transformation completed. Initial: %s, Final: %s, Removed: %s.",
        initial_count,
        len(df),
        initial_count - len(df)
    )

    return df
