
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from pipeline.load import load_into_postgres, DATA_COLUMNS


def sample_data():
    return pd.DataFrame({
        "id": [101],
        "date_time": [pd.Timestamp("2026-11-01 10:30:00")],
        "type": ["ARREST"],
        "subtype": ["WARRANT"],
        "location": ["Cambridge"],
        "description": ["Test incident"],
        "last_updated": [pd.Timestamp("2026-11-01 11:00:00")],
        "year": [2026],
        "month": [11],
        "day": [1],
        "hour": [10],
        "minute": [30],
        "second": [0],
        "day_of_week": ["Sunday"]
    })


def test_load_empty_dataframe():
    with patch("pipeline.load.create_database_engine") as mock_engine:
        load_into_postgres(pd.DataFrame())

        mock_engine.assert_not_called()


def test_load_missing_columns():
    df = sample_data().drop(columns=["location"])

    with pytest.raises(ValueError, match="Missing transformed columns"):
        load_into_postgres(df)


@patch("pipeline.load.create_database_engine")
@patch("pipeline.load.create_postgres_table")
def test_load_success(mock_create_table, mock_create_engine):
    engine = MagicMock()
    connection = MagicMock()

    mock_create_engine.return_value = engine
    engine.begin.return_value.__enter__.return_value = connection

    with patch.object(pd.DataFrame, "to_sql") as mock_to_sql:
        load_into_postgres(sample_data())

    mock_create_table.assert_called_once_with(engine)
    mock_to_sql.assert_called_once()

    kwargs = mock_to_sql.call_args.kwargs

    assert kwargs["name"] == "cpd_incidents"
    assert kwargs["if_exists"] == "append"
    assert kwargs["index"] is False

    engine.dispose.assert_called_once()
