"""Tests for the fake plant data generator."""

import datetime as dt

import pytest

from src.python.load_data import fake_data

START = dt.datetime(2022, 1, 1)
END = dt.datetime(2022, 2, 1)


def test_when_generating_then_has_timestamp_sensors_and_target():
    data = fake_data.generate_plant_data(start=START, end=END)

    assert "timestamp" in data.columns
    assert fake_data.TARGET_COLUMN in data.columns
    for sensor in fake_data.SENSOR_PROFILES:
        assert sensor in data.columns


def test_when_generating_then_one_row_per_hour():
    data = fake_data.generate_plant_data(start=START, end=END)

    # January has 31 days, and the end is exclusive.
    assert len(data) == 31 * 24


def test_when_generating_then_no_missing_values():
    """The dashboard divides and plots these, so nulls would show up badly."""
    data = fake_data.generate_plant_data(start=START, end=END)

    assert data.isna().sum().sum() == 0


def test_when_same_seed_then_same_data():
    """Reproducibility: a score seen today must be the same tomorrow."""
    first = fake_data.generate_plant_data(start=START, end=END, seed=7)
    second = fake_data.generate_plant_data(start=START, end=END, seed=7)

    assert first.equals(second)


def test_when_different_seed_then_different_data():
    first = fake_data.generate_plant_data(start=START, end=END, seed=1)
    second = fake_data.generate_plant_data(start=START, end=END, seed=2)

    assert not first.equals(second)


def test_when_start_after_end_then_raises():
    with pytest.raises(ValueError, match="must be before"):
        fake_data.generate_plant_data(start=END, end=START)


def test_when_range_shorter_than_one_reading_then_returns_one_row():
    """A sub-hour range still contains the reading taken at `start`."""
    data = fake_data.generate_plant_data(start=START, end=START + dt.timedelta(minutes=30))

    assert len(data) == 1


@pytest.mark.parametrize("sensor", sorted(fake_data.SENSOR_PROFILES))
def test_when_generating_then_sensors_sit_near_their_profile(sensor: str):
    """Values must be plausible, or the dashboard's numbers look wrong."""
    data = fake_data.generate_plant_data(start=START, end=END)
    mean, deviation = fake_data.SENSOR_PROFILES[sensor]

    # Within four standard deviations of the intended mean is generous but
    # still catches a sensor generated at the wrong scale entirely.
    assert abs(data[sensor].mean() - mean) < 4 * deviation
    assert data[sensor].std() > 0


def test_when_generating_then_target_is_learnable():
    """The whole point: a model must be able to find the signal.

    If this fails, the dashboard would show a near-zero R² and look broken.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    from sklearn.model_selection import train_test_split

    data = fake_data.generate_plant_data(start=START, end=dt.datetime(2023, 1, 1))
    x = data[list(fake_data.SENSOR_PROFILES)]
    y = data[fake_data.TARGET_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, shuffle=False)

    model = LinearRegression().fit(x_train, y_train)

    # Comfortably learnable, but the noise stops it being perfect -- which is
    # the honest lesson about how models behave on real data.
    r_squared = r2_score(y_test, model.predict(x_test))
    assert 0.5 < r_squared < 0.99


def test_when_generating_a_year_then_covers_twelve_months():
    """The dashboard charts error per month, so it needs months to chart."""
    data = fake_data.generate_plant_data(start=START, end=dt.datetime(2023, 1, 1))

    assert data["timestamp"].dt.month.nunique() == 12
