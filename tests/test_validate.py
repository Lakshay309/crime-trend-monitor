
import pandas as pd
import pytest

from pipeline.validate import (
    validate_schema,
    validate_id,
    validate_datetime,
    validate_required_fields,
    validate_data
)


def sample_data():
    return pd.DataFrame({
        "date_time": ["2026-11-01 10:30:00"],
        "id": ["123"],
        "type": ["ARREST"],
        "subtype": ["WARRANT"],
        "location": ["Cambridge"],
        "last_updated": ["2026-11-01 11:00:00"],
        "description": ["Test incident"]
    })


def test_validate_schema_success():
    validate_schema(sample_data())


def test_validate_schema_missing_column():
    df = sample_data().drop(columns=["location"])

    with pytest.raises(ValueError, match="Missing expected columns"):
        validate_schema(df)


def test_validate_id_converts_numeric_values():
    df = sample_data()
    result = validate_id(df)

    assert result["id"].iloc[0] == 123


def test_validate_id_invalid_value():
    df = sample_data()
    df.loc[0, "id"] = "invalid"

    result = validate_id(df)

    assert pd.isna(result["id"].iloc[0])


def test_validate_datetime_parses_values():
    result = validate_datetime(sample_data())

    assert pd.api.types.is_datetime64_any_dtype(result["date_time"])


def test_validate_datetime_invalid_value():
    df = sample_data()
    df.loc[0, "date_time"] = "invalid-date"

    result = validate_datetime(df)

    assert pd.isna(result["date_time"].iloc[0])


def test_validate_required_fields_does_not_raise():
    validate_required_fields(sample_data())


def test_validate_data_success():
    result = validate_data(sample_data())

    assert len(result) == 1
    assert result["id"].iloc[0] == 123
    assert "description" in result.columns


def test_validate_data_empty_dataframe():
    with pytest.raises(ValueError, match="empty"):
        validate_data(pd.DataFrame())
