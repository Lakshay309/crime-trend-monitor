
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    create_engine,
    func,
    MetaData,
    Table,
)
from sqlalchemy.engine import URL
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from pipeline.config import settings

logger = logging.getLogger("crime_pipeline.load")

TABLE_NAME = "cpd_incidents"

DATA_COLUMNS = [
    "id",
    "date_time",
    "type",
    "subtype",
    "location",
    "description",
    "last_updated",
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "day_of_week",
]


def create_database_engine():
    """Create the configured database engine."""

    if settings.database_type == "sqlite":
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )

    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_database_table(engine):
    """Create the incident table and indexes."""

    schema_path = (
        Path(__file__).resolve().parent.parent
        / "sql"
        / "schema.sql"
    )

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Database schema file not found: {schema_path}"
        )

    schema_sql = schema_path.read_text(encoding="utf-8-sig")

    with engine.begin() as connection:
        for statement in schema_sql.split(";"):
            if statement.strip():
                connection.exec_driver_sql(statement)

    logger.info(
        "%s table and indexes are ready.",
        settings.database_type.upper(),
    )


def upsert_incidents(table, connection, keys, data_iter):
    """Insert new incidents and update existing incidents."""

    records = [
        dict(zip(keys, row))
        for row in data_iter
    ]

    if not records:
        return 0

    metadata = MetaData()

    db_table = Table(
        TABLE_NAME,
        metadata,
        autoload_with=connection,
    )

    if connection.dialect.name == "sqlite":
        insert_statement = sqlite_insert(db_table)
    else:
        insert_statement = pg_insert(db_table)

    statement = insert_statement.values(records)

    update_columns = {
        column: statement.excluded[column]
        for column in keys
        if column != "id"
    }

    update_columns[db_table.c.updated_at] = func.current_timestamp()

    statement = statement.on_conflict_do_update(
        index_elements=[db_table.c.id],
        set_=update_columns,
    )

    result = connection.execute(statement)

    return result.rowcount


def load_data(df):
    """Load transformed incidents using database-specific UPSERT."""

    if df.empty:
        logger.warning("No records to load.")
        return

    missing_columns = set(DATA_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing transformed columns: {sorted(missing_columns)}"
        )

    df = df[DATA_COLUMNS].copy()

    engine = create_database_engine()

    try:
        create_database_table(engine)

        logger.info(
            "Loading %s records into %s.",
            len(df),
            settings.database_type.upper(),
        )

        with engine.begin() as connection:
            df.to_sql(
                name=TABLE_NAME,
                con=connection,
                if_exists="append",
                index=False,
                chunksize=60 if settings.database_type == "sqlite" else settings.batch_size,
                method=upsert_incidents,
            )

        logger.info(
            "Successfully processed %s records.",
            len(df),
        )

    except Exception:
        logger.exception("Database loading failed.")
        raise

    finally:
        engine.dispose()
        logger.info("Database connection pool disposed.")
