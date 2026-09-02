"""Load plant sensor data from ClickHouse (Phase 1).

Connection details are read from the environment so that no credentials
are ever committed to the repo:

    CLICKHOUSE_HOST      e.g. abc123.eu-west-2.aws.clickhouse.cloud
    CLICKHOUSE_PORT      defaults to 8443
    CLICKHOUSE_USER
    CLICKHOUSE_PASSWORD
    CLICKHOUSE_DATABASE
"""

import dataclasses
import datetime as dt
import os

import clickhouse_connect
import pandas as pd

DEFAULT_PORT = 8443


@dataclasses.dataclass(frozen=True)
class ClickHouseConfig:
    """Everything needed to open a ClickHouse connection."""

    host: str
    user: str
    password: str
    database: str
    port: int = DEFAULT_PORT

    @classmethod
    def from_environment(cls) -> "ClickHouseConfig":
        return cls(
            host=_required_environment_variable("CLICKHOUSE_HOST"),
            user=_required_environment_variable("CLICKHOUSE_USER"),
            password=_required_environment_variable("CLICKHOUSE_PASSWORD"),
            database=_required_environment_variable("CLICKHOUSE_DATABASE"),
            port=int(os.environ.get("CLICKHOUSE_PORT", DEFAULT_PORT)),
        )


def _required_environment_variable(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"environment variable {name!r} must be set to connect to ClickHouse")
    return value


class PlantDataLoader:
    """Reads plant sensor data out of ClickHouse."""

    def __init__(self, config: ClickHouseConfig) -> None:
        self._config = config

    def load(
        self,
        table: str,
        features: list[str],
        start: dt.datetime,
        end: dt.datetime,
    ) -> pd.DataFrame:
        """Return the given features between start and end, ordered by time.

        Always pass a start and an end -- the plant tables are large, and an
        unbounded query will take a very long time.
        """
        if start >= end:
            raise ValueError(f"start {start!r} must be before end {end!r}")
        if not features:
            raise ValueError("features must not be empty")

        query = self._build_query(table=table, features=features)
        with clickhouse_connect.get_client(
            host=self._config.host,
            port=self._config.port,
            username=self._config.user,
            password=self._config.password,
            database=self._config.database,
        ) as client:
            return client.query_df(query, parameters={"start": start, "end": end})

    def _build_query(self, table: str, features: list[str]  ) -> str:
        columns = ", ".join(["timestamp", *features])
        return (
            f"SELECT {columns} FROM {table} "
            "WHERE timestamp >= %(start)s AND timestamp < %(end)s "
            "ORDER BY timestamp"
        )
