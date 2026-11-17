
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from pipeline.extract import extract_data


@patch("pipeline.extract.Socrata")
def test_extract_data_success(mock_socrata):
    client = MagicMock()
    mock_socrata.return_value = client

    client.get.side_effect = [
        [{"id": "1"}, {"id": "2"}],
        []
    ]

    with patch("pipeline.extract.settings") as mock_settings:
        mock_settings.socrata_app_token = "test-token"
        mock_settings.socrata_domain = "data.cambridgema.gov"
        mock_settings.socrata_dataset_id = "test-dataset"
        mock_settings.batch_size = 5000

        result = extract_data()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result["id"]) == ["1", "2"]
    client.close.assert_called_once()


@patch("pipeline.extract.Socrata")
def test_extract_data_empty_response(mock_socrata):
    client = MagicMock()
    mock_socrata.return_value = client
    client.get.return_value = []

    with patch("pipeline.extract.settings") as mock_settings:
        mock_settings.socrata_app_token = "test-token"
        mock_settings.socrata_domain = "data.cambridgema.gov"
        mock_settings.socrata_dataset_id = "test-dataset"
        mock_settings.batch_size = 5000

        result = extract_data()

    assert result.empty
    client.close.assert_called_once()


def test_extract_data_missing_token():
    with patch("pipeline.extract.settings") as mock_settings:
        mock_settings.socrata_app_token = None

        with pytest.raises(ValueError, match="SOCRATA_APP_TOKEN"):
            extract_data()
