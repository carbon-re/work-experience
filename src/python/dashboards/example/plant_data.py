"""Turning training output into the shapes a dashboard can chart.

**The important idea in this file.** A dashboard should not load data or train
models. It should be handed **DataFrames that already exist in memory** and
just draw them. That is why the useful function here is `build_results`: you
give it the DataFrames your training code already produced, and it gives back
a `ModelResults` the charts can render.

So when you wire your own work from `src/python/main.py` into a dashboard, you
do **not** rewrite any of this. Your loop already has the pieces:

    # in your own training code
    model, x_test, y_test = train_model(data)
    predicted = model.predict(x_test)

    results = plant_data.build_results(
        predictions=pd.DataFrame(
            {
                "timestamp": data.loc[x_test.index, "timestamp"],
                "actual": y_test,
                "predicted": predicted,
            }
        ),
        feature_importances=pd.DataFrame(
            {"feature": features, "importance": abs(model.coef_)}
        ),
        train_row_count=len(x_test) * 4,
    )

Nothing is written to disk and nothing is re-read. The DataFrame in your
Python process is passed straight to the dashboard.

The CSV loading further down (`load_example_data`) exists only so that *this
example* has something to show without needing your ClickHouse credentials.
Think of it as a stand-in for your own `data_load()` -- it is the one part you
would replace.

`build_results` produces four data shapes, and each one suits a different kind
of chart:

* a time series -> line chart
* actual-vs-predicted pairs -> scatter plot
* one error number per month -> bar chart
* one number per feature -> horizontal bar chart

See `app.py` for the charts themselves.
"""

import dataclasses
import datetime as dt
import pathlib

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split

# Plants we have sample CSVs for, with a friendly name and the story behind
# each one. The READMEs next to the CSVs have the full version.
PLANTS: dict[str, str] = {
    "abc": "Al Buraimi Cement - coal only, the simple case",
    "bcd": "Bharat Cement Development - has a kiln shutdown in the data",
    "cde": "Cemento del Este - burns coal and RDF together",
    "def": "Dynamic Eco Formworks - petcoke and RDF, NCV in mixed units",
}

# Feed rates below this are the weigh scales' noise floor, not real
# production. Dividing by them produces nonsense SHC, so we drop those rows
# (this is the trap the BCD README warns about).
MIN_MEAL_TPUT_TPH = 10.0

# NCV columns for DEF are recorded in GJ/t while everything else is kcal/kg.
KCAL_PER_KG_PER_GJ_PER_TONNE = 238.85

TARGET = "shc"
TEST_FRACTION = 0.2
RANDOM_SEED = 42


@dataclasses.dataclass(frozen=True)
class ModelResults:
    """Everything the dashboard needs to draw its charts."""

    predictions: pd.DataFrame  # timestamp, actual, predicted, error
    monthly_errors: pd.DataFrame  # month, mae, sample_count
    feature_importances: pd.DataFrame  # feature, importance
    mean_absolute_error: float
    root_mean_squared_error: float
    r_squared: float
    train_row_count: int
    test_row_count: int


def build_results(
    predictions: pd.DataFrame,
    feature_importances: pd.DataFrame,
    train_row_count: int,
) -> ModelResults:
    """Package up in-memory DataFrames into something the charts can draw.

    **This is the function to call from your own code.** It does no loading,
    no training and no file access -- it takes DataFrames you already hold in
    memory, checks they have the columns the charts need, and computes the
    summaries (error column, monthly errors, scores) on top.

    Args:
        predictions: one row per test sample, with columns `timestamp`,
            `actual` and `predicted`. A `month` column is added if absent,
            and an `error` column is always recomputed.
        feature_importances: columns `feature` and `importance`, one row per
            input feature. For a linear model use `abs(model.coef_)`; for a
            random forest use `model.feature_importances_`.
        train_row_count: how many rows the model was trained on. Only used to
            display alongside the test count, so a reader can judge the split.

    Returns:
        A frozen `ModelResults` holding every shape `app.py` charts.
    """
    _check_columns(predictions, required={"timestamp", "actual", "predicted"})
    _check_columns(feature_importances, required={"feature", "importance"})
    if predictions.empty:
        raise ValueError("predictions must not be empty -- there is nothing to chart")

    # Copy before adding columns: a function handed a DataFrame should not
    # quietly modify the caller's copy.
    predictions = predictions.copy()
    predictions["error"] = predictions["predicted"] - predictions["actual"]
    if "month" not in predictions.columns:
        predictions["month"] = predictions["timestamp"].dt.to_period("M").dt.to_timestamp()

    ordered_importances = feature_importances.sort_values(
        "importance", ascending=False
    ).reset_index(drop=True)

    return ModelResults(
        predictions=predictions,
        monthly_errors=_summarise_by_month(predictions),
        feature_importances=ordered_importances,
        mean_absolute_error=float(
            mean_absolute_error(predictions["actual"], predictions["predicted"])
        ),
        root_mean_squared_error=float(
            root_mean_squared_error(predictions["actual"], predictions["predicted"])
        ),
        r_squared=float(r2_score(predictions["actual"], predictions["predicted"])),
        train_row_count=train_row_count,
        test_row_count=len(predictions),
    )


def _check_columns(data: pd.DataFrame, required: set[str]) -> None:
    """Fail early and clearly if a caller's DataFrame is the wrong shape."""
    missing = required - set(data.columns)
    if missing:
        raise ValueError(
            f"DataFrame is missing required column(s) {sorted(missing)}; "
            f"got columns {sorted(data.columns)}"
        )


def load_example_data(plant_ref: str) -> pd.DataFrame:
    """Read one plant's sample CSV and add an `shc` column.

    **This is the part you would replace** with your own `data_load()` from
    `main.py`. It exists so the example has data to show without needing
    ClickHouse credentials.

    Args:
        plant_ref: one of the keys of `PLANTS`, e.g. "abc".

    Returns:
        The raw columns from the CSV, plus `shc` (kcal/kg) and `month`.
    """
    if plant_ref not in PLANTS:
        raise ValueError(f"plant_ref must be one of {sorted(PLANTS)}, got {plant_ref!r}")

    data = pd.read_csv(_csv_path(plant_ref), parse_dates=["timestamp"])
    data = _drop_shutdown_rows(data)
    data[TARGET] = _calculate_shc(data)
    data["month"] = data["timestamp"].dt.to_period("M").dt.to_timestamp()
    return data.dropna(subset=[TARGET]).reset_index(drop=True)


def _csv_path(plant_ref: str) -> pathlib.Path:
    """Locate a sample CSV.

    The CSVs live in `src/infra/plant-data/`, which is a Terraform directory
    and not an importable Python package, so we cannot use
    `importlib.resources`. Pants puts them in the sandbox at that same path
    (see the `csvs` target in src/infra/plant-data/BUILD), and
    this file sits four levels below the repo root.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[4]
    return repo_root / "src" / "infra" / "plant-data" / f"{plant_ref}.csv"


def _drop_shutdown_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where the kiln was not really running."""
    return data[data["s_ph_sil_tput"] > MIN_MEAL_TPUT_TPH].copy()


def fuel_columns(data: pd.DataFrame) -> list[str]:
    """Return the fuel throughput columns present in this plant's data."""
    return [
        column
        for column in data.columns
        if column.startswith("f_k_") and column.endswith("_tput")
    ]


def _calculate_shc(data: pd.DataFrame) -> pd.Series:
    """Specific heat consumption in kcal per kg of meal.

    SHC = total energy in / mass of material out. Each fuel contributes
    its throughput multiplied by its net calorific value.
    """
    total_energy_kcal_per_hour = pd.Series(0.0, index=data.index)
    for fuel_column in fuel_columns(data):
        ncv_column = fuel_column.replace("_tput", "_ncv")
        ncv_kcal_per_kg = _normalise_ncv(data[ncv_column], ncv_column)
        # tonnes/h * 1000 kg/t * kcal/kg -> kcal/h
        total_energy_kcal_per_hour += data[fuel_column] * 1000 * ncv_kcal_per_kg

    meal_kg_per_hour = data["s_ph_sil_tput"] * 1000
    return total_energy_kcal_per_hour / meal_kg_per_hour


def _normalise_ncv(ncv: pd.Series, ncv_column: str) -> pd.Series:
    """Convert an NCV column to kcal/kg.

    DEF records RDF calorific value in GJ/t; everything else is already
    kcal/kg. We spot the GJ/t case by magnitude -- real kcal/kg values for
    any fuel we burn are in the thousands.
    """
    # NCV is often reported only when it changes, leaving gaps to fill.
    filled = ncv.ffill().bfill()
    if filled.median() < 100:
        return filled * KCAL_PER_KG_PER_GJ_PER_TONNE
    return filled


def train_and_score(
    data: pd.DataFrame,
    model_name: str = "Random forest",
) -> ModelResults:
    """Train a model on a DataFrame and package the results for charting.

    This stands in for the training code you already have in `main.py`. Note
    what it does at the end: it builds two plain DataFrames in memory and
    hands them to `build_results`. Your own code should do the same -- the
    dashboard never needs to know how the model was trained.

    The split is chronological (`shuffle=False`), not random: predicting the
    past from the future would flatter the model and tell us nothing about
    how it will behave tomorrow.
    """
    features = fuel_columns(data) + ["s_ph_sil_tput"]
    x = data[features]
    y = data[TARGET]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_FRACTION, shuffle=False
    )
    model = _build_model(model_name)
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)

    # Everything below is just repackaging in-memory objects. No files.
    return build_results(
        predictions=pd.DataFrame(
            {
                "timestamp": data.loc[x_test.index, "timestamp"],
                "actual": y_test,
                "predicted": predicted,
            }
        ),
        feature_importances=_extract_importances(model, features),
        train_row_count=len(x_train),
    )


def _build_model(model_name: str) -> LinearRegression | RandomForestRegressor:
    if model_name == "Linear regression":
        return LinearRegression()
    if model_name == "Random forest":
        return RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
    raise ValueError(f"unknown model_name {model_name!r}")


def _summarise_by_month(predictions: pd.DataFrame) -> pd.DataFrame:
    """Mean absolute error per calendar month, as `main.py` computes."""
    grouped = predictions.groupby("month")
    summary = grouped.apply(
        lambda group: mean_absolute_error(group["actual"], group["predicted"]),
        include_groups=False,
    )
    return pd.DataFrame(
        {
            "month": summary.index,
            "mae": summary.to_numpy(),
            "sample_count": grouped.size().to_numpy(),
        }
    )


def _extract_importances(
    model: LinearRegression | RandomForestRegressor,
    features: list[str],
) -> pd.DataFrame:
    """One importance number per feature, largest first.

    A random forest exposes `feature_importances_`. A linear model does not,
    so we use the absolute coefficient -- a rough stand-in, and only
    comparable across features because they are on similar scales here.
    """
    if isinstance(model, RandomForestRegressor):
        importances = model.feature_importances_
    else:
        importances = abs(model.coef_)

    # No sorting here -- build_results orders them for the chart.
    return pd.DataFrame({"feature": features, "importance": importances})


def date_range(data: pd.DataFrame) -> tuple[dt.date, dt.date]:
    """First and last timestamp in the data, as dates."""
    return data["timestamp"].min().date(), data["timestamp"].max().date()
