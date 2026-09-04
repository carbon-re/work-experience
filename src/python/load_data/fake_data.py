"""Generate realistic-looking fake plant data.

Why this exists: the real plant data lives in ClickHouse, which needs a
password and a network connection. This module makes up data with the same
*shape* and roughly the same behaviour, so the dashboard and the model work
on any machine with no credentials at all.

It is **not** real plant data. The numbers are invented. What is real is the
structure: the same column names, plausible ranges and units, and genuine
relationships between the sensors and the target -- so a model trained on it
actually learns something, and the dashboard has something believable to draw.

The data is generated from a fixed random seed, so you get the same numbers
every time you run it. That means a score you see today is the same score you
will see tomorrow, which makes it much easier to tell whether a change you
made actually did anything.
"""

import datetime as dt

import numpy as np
import pandas as pd

# Same seed every run, so results are reproducible.
RANDOM_SEED = 42

# One reading per hour, matching how the real plant data is sampled.
READING_INTERVAL = dt.timedelta(hours=1)

# Each sensor gets a plausible average and a spread, in its real units.
# (mean, standard deviation)
SENSOR_PROFILES: dict[str, tuple[float, float]] = {
    "g_k_pyro_temp": (1050.0, 25.0),  # kiln burning-zone temperature, C
    "p_k_torque": (65.0, 8.0),  # kiln drive torque, %
    "p_c_grate_speed": (12.0, 1.5),  # clinker cooler grate speed, strokes/min
    "g_ph_cy4_gol_temp": (860.0, 20.0),  # preheater cyclone 4 gas outlet, C
    "g_ph_cy3_gol_temp": (720.0, 18.0),  # preheater cyclone 3 gas outlet, C
    "g_ph_gol_temp": (330.0, 15.0),  # preheater gas outlet, C
    "f_k_coal_tput": (13.0, 1.8),  # kiln coal feed, tonnes/hour
    "g_pc_pyro_temp": (890.0, 22.0),  # precalciner temperature, C
    "g_pc_wall_scc_temp4": (410.0, 18.0),  # precalciner wall temperature, C
    "s_ph_sil_cao": (43.0, 1.2),  # CaO in raw meal, %
    "s_ph_sil_al2o3": (3.4, 0.3),  # Al2O3 in raw meal, %
    "s_ph_sil_fe2o3": (2.1, 0.2),  # Fe2O3 in raw meal, %
    "s_ph_sil_sio2": (13.5, 0.8),  # SiO2 in raw meal, %
}

# How strongly each sensor pushes the target up or down. These are what make
# the data learnable: without them the target would be pure noise and no
# model could ever score above zero.
TARGET_WEIGHTS: dict[str, float] = {
    "f_k_coal_tput": 42.0,  # more fuel -> more power drawn
    "p_k_torque": 8.0,  # a harder-working kiln draws more
    "g_k_pyro_temp": 1.1,  # a hotter kiln costs more to keep hot
    "g_pc_pyro_temp": 0.6,
    "p_c_grate_speed": 15.0,
    "g_ph_cy4_gol_temp": 0.35,
    "g_ph_cy3_gol_temp": 0.2,
    "g_ph_gol_temp": -0.45,  # heat out the back is heat wasted
    "g_pc_wall_scc_temp4": 0.15,
    "s_ph_sil_cao": 6.0,  # harder-to-burn meal costs more energy
    "s_ph_sil_al2o3": -4.0,
    "s_ph_sil_fe2o3": -3.0,
    "s_ph_sil_sio2": 2.5,
}

TARGET_COLUMN = "p_k_power"

# Noise on the target, as a fraction of its spread. Some noise is essential:
# with none, a linear model would score a perfect 1.00, which would teach
# entirely the wrong lesson about how models behave on real data.
TARGET_NOISE_FRACTION = 0.28

# A plant does not sit at one steady state all year -- it drifts with the
# seasons, the weather and the raw material. This is the size of that drift
# as a fraction of each sensor's spread.
SEASONAL_DRIFT_FRACTION = 0.55


def generate_plant_data(
    start: dt.datetime,
    end: dt.datetime,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Make up hourly plant data between two dates.

    Args:
        start: first reading (inclusive).
        end: last reading (exclusive).
        seed: random seed. The same seed always gives the same data.

    Returns:
        A DataFrame with a `timestamp` column, one column per sensor, and the
        target column `p_k_power` -- the same columns the real loader returns.
    """
    if start >= end:
        raise ValueError(f"start {start!r} must be before end {end!r}")

    # `inclusive="left"` excludes the end, matching how the real loader
    # queries ClickHouse. Any span shorter than the interval still yields one
    # reading, at `start`.
    timestamps = pd.date_range(start=start, end=end, freq=READING_INTERVAL, inclusive="left")

    generator = np.random.default_rng(seed)
    data = pd.DataFrame({"timestamp": timestamps})
    seasonal_cycle = _seasonal_cycle(timestamps)

    for sensor, (mean, deviation) in SENSOR_PROFILES.items():
        data[sensor] = _generate_sensor(
            generator=generator,
            mean=mean,
            deviation=deviation,
            seasonal_cycle=seasonal_cycle,
        )

    data[TARGET_COLUMN] = _generate_target(data, generator)
    return data


def _seasonal_cycle(timestamps: pd.DatetimeIndex) -> np.ndarray:
    """A smooth yearly wave, in roughly -1..+1.

    Gives the data structure that varies month to month, so the dashboard's
    per-month chart has something real to show rather than a flat line.
    """
    day_of_year = timestamps.dayofyear.to_numpy()
    return np.sin(2 * np.pi * day_of_year / 365.25)


def _generate_sensor(
    generator: np.random.Generator,
    mean: float,
    deviation: float,
    seasonal_cycle: np.ndarray,
) -> np.ndarray:
    """One sensor's readings: a seasonal trend plus correlated noise."""
    seasonal_offset = seasonal_cycle * deviation * SEASONAL_DRIFT_FRACTION
    wobble = _smoothed_noise(generator, length=len(seasonal_cycle)) * deviation
    return mean + seasonal_offset + wobble


def _smoothed_noise(generator: np.random.Generator, length: int, window: int = 6) -> np.ndarray:
    """Noise that drifts rather than jumping about.

    Real sensor readings are correlated in time: if the kiln is hot now, it
    is probably still hot in an hour. Independent random values per row would
    look nothing like a real plant, so we smooth them with a rolling mean.
    """
    raw = generator.standard_normal(length + window)
    smoothed = pd.Series(raw).rolling(window=window, min_periods=1).mean()
    trimmed = smoothed.iloc[window:].to_numpy()
    # Rolling means have a smaller spread than what went in; rescale so the
    # caller still gets roughly one standard deviation.
    spread = trimmed.std()
    if spread == 0:
        return trimmed
    return trimmed / spread


def _generate_target(data: pd.DataFrame, generator: np.random.Generator) -> np.ndarray:
    """Build the target from the sensors, then add noise.

    This is the relationship the model has to rediscover. Because we build it
    from a weighted sum, a linear model can find most of it -- but the noise
    means it can never be perfect, which is realistic.
    """
    contributions = np.zeros(len(data))
    for sensor, weight in TARGET_WEIGHTS.items():
        centred = data[sensor] - SENSOR_PROFILES[sensor][0]
        contributions += centred.to_numpy() * weight

    baseline = 4200.0
    noise_scale = contributions.std() * TARGET_NOISE_FRACTION
    noise = generator.standard_normal(len(data)) * noise_scale
    return baseline + contributions + noise
