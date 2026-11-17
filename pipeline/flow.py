import logging

from prefect import flow, task

from pipeline.extract import extract_data
from pipeline.validate import validate_data
from pipeline.transform import transform_data
from pipeline.load import load_into_postgres
from pipeline.logging_config import logger


@task(
    name="Extract Crime Data",
    retries=2,
    retry_delay_seconds=30,
)
def extract_task():
    """Fetch crime records from the Socrata API."""

    return extract_data()


@task(
    name="Validate Crime Data",
    retries=1,
    retry_delay_seconds=10,
)
def validate_task(df):
    """Validate the extracted records."""

    return validate_data(df)


@task(
    name="Transform Crime Data",
)
def transform_task(df):
    """Clean records and generate analytical features."""

    return transform_data(df)


@task(
    name="Load Crime Data",
    retries=2,
    retry_delay_seconds=30,
)
def load_task(df):
    """Load transformed records into PostgreSQL."""

    load_into_postgres(df)

    return len(df)


@flow(
    name="Cambridge Crime Monitoring Pipeline",
    description=(
        "Extract, validate, transform and load "
        "Cambridge Police incident records."
    ),
    log_prints=True,
)
def crime_pipeline():
    """Execute the complete crime monitoring ETL pipeline."""

    logger.info("Crime monitoring pipeline started.")

    raw_data = extract_task()

    validated_data = validate_task(raw_data)

    transformed_data = transform_task(validated_data)

    loaded_count = load_task(transformed_data)

    logger.info(
        "Pipeline completed successfully. "
        "Records processed: %s.",
        loaded_count,
    )

    return {
        "status": "success",
        "records_processed": loaded_count,
    }


if __name__ == "__main__":
    crime_pipeline()
