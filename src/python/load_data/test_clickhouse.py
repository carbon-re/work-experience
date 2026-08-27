import datetime as dt

import pytest

from src.python.load_data.clickhouse import ClickHouseConfig, PlantDataLoader

A_CONFIG = ClickHouseConfig(
    host="localhost",
    user="student",
    password="not-a-real-password",
    database="mokra",
)


def test_when_start_is_after_end_then_raises():
    loader = PlantDataLoader(A_CONFIG)

    with pytest.raises(ValueError, match="must be before"):
        loader.load(
            table="mokra",
            features=["s_ph_sil_tput"],
            start=dt.datetime(2023, 2, 1),
            end=dt.datetime(2023, 1, 1),
        )


def test_when_no_features_requested_then_raises():
    loader = PlantDataLoader(A_CONFIG)

    with pytest.raises(ValueError, match="features must not be empty"):
        loader.load(
            table="mokra",
            features=[],
            start=dt.datetime(2023, 1, 1),
            end=dt.datetime(2023, 2, 1),
        )


def test_query_selects_timestamp_and_requested_features():
    loader = PlantDataLoader(A_CONFIG)

    query = loader._build_query(table="mokra", features=["f_k_coal_tput"])

    assert "SELECT timestamp, f_k_coal_tput FROM mokra" in query
    assert "ORDER BY timestamp" in query


def test_config_from_environment_reports_the_missing_variable(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)

    with pytest.raises(ValueError, match="CLICKHOUSE_HOST"):
        ClickHouseConfig.from_environment()
