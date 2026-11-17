
import pandas as pd
import pytest

from pipeline.transform import (
    remove_invalid_rows,
    remove_duplicates,
    normalize_data_types,
    create_datetime_features,
    transform_data
)


def sample_data():
    return pd.DataFrame({
        "date_time": [
            "2026-11-01 10:30:45",
            "2026-11-02 14:20:10"
        ],
        "id": ["101", "102"],
        "type": ["ARREST", "INCIDENT"],
        "subtype": ["WARRANT", "THEFT"],
        "location": ["Cambridge", "Harvard Square"],
        "last_updated": [
            "2026-11-01 11:00:00",
            "2026-11-02 15:00:00"
        ],
        "description": ["Test 1", "Test 2"]
    })


def test_remove_invalid_rows():
    df = sample_data()
    df.loc[0, "location"] = None

    result = remove_invalid_rows(df)

    assert len(result) == 1


def test_remove_duplicates():
    df = sample_data()
    duplicate = df.iloc[[0]]

    df = pd.concat([df, duplicate], ignore_index=True)

    result = remove_duplicates(df)

    assert len(result) == 2
    assert result["id"].is_unique


def test_normalize_data_types():
    result = normalize_data_types(sample_data())

    assert result["id"].dtype == "int64"
    assert pd.api.types.is_datetime64_any_dtype(result["date_time"])
    assert pd.api.types.is_datetime64_any_dtype(result["last_updated"])


def test_create_datetime_features():
    df = sample_data()
    df = normalize_data_types(df)

    result = create_datetime_features(df)

    assert result["year"].iloc[0] == 2026
    assert result["month"].iloc[0] == 11
    assert result["day"].iloc[0] == 1
    assert result["hour"].iloc[0] == 10
    assert result["minute"].iloc[0] == 30
    assert result["second"].iloc[0] == 45
    assert result["day_of_week"].iloc[0] == "Sunday"


def test_transform_data_success():
    result = transform_data(sample_data())

    assert len(result) == 2
    assert result["id"].is_unique
    assert "year" in result.columns
    assert "month" in result.columns
    assert "day_of_week" in result.columns


def test_transform_data_empty_dataframe():
    with pytest.raises(ValueError, match="empty"):
        transform_data(pd.DataFrame())


def test_transform_data_removes_invalid_timestamps():
    df = sample_data()
    df.loc[0, "date_time"] = "invalid-date"

    result = transform_data(df)

    assert len(result) == 1
    assert result["date_time"].notna().all()
