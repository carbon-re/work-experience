from importlib import resources as impresources

import pandas as pd
import pytest


@pytest.fixture
def test_data():
    """
    This fixture will allow a test to load any csv file in the
    test data directory of soft_sensors.
    """

    def _(filename: str) -> pd.DataFrame:
        data_path = impresources.files(__package__) / "soft_sensors/test_data" / filename
        return pd.read_csv(str(data_path))

    return _
