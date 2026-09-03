"""Tests for the example dashboard's data loading and modelling."""

import dataclasses

import pandas as pd
import pytest

from src.python.dashboards.example import plant_data


def test_when_plant_ref_unknown_then_raises():
    with pytest.raises(ValueError, match="plant_ref must be one of"):
        plant_data.load_example_data("nope")


@pytest.mark.parametrize("plant_ref", sorted(plant_data.PLANTS))
def test_when_loading_any_sample_plant_then_gets_usable_shc(plant_ref: str):
    data = plant_data.load_example_data(plant_ref)

    assert not data.empty
    assert data["shc"].notna().all()
    # Real cement plants run somewhere around 700-1100 kcal/kg. This is a wide
    # net: it catches unit mix-ups and divide-by-almost-zero, not fine detail.
    assert data["shc"].between(400, 2000).all()


def test_when_meal_throughput_near_zero_then_row_dropped():
    """The shutdown trap: tiny feed values give nonsensical SHC."""
    data = plant_data.load_example_data("bcd")

    assert (data["s_ph_sil_tput"] > plant_data.MIN_MEAL_TPUT_TPH).all()


def test_when_ncv_in_gigajoules_then_converted_to_kcal_per_kg():
    """DEF reports RDF calorific value in GJ/t, everything else in kcal/kg."""
    gigajoule_values = pd.Series([22.5, 23.0, 22.8])

    converted = plant_data._normalise_ncv(gigajoule_values, "f_k_rdf_ncv")

    assert converted.median() == pytest.approx(22.8 * 238.85, rel=1e-6)


def test_when_ncv_already_kcal_then_left_alone():
    kcal_values = pd.Series([5500.0, 6000.0])

    converted = plant_data._normalise_ncv(kcal_values, "f_k_coal_ncv")

    assert converted.tolist() == [5500.0, 6000.0]


def test_when_ncv_has_gaps_then_filled_forward():
    """Plants often send NCV only when it changes."""
    sparse = pd.Series([None, 5500.0, None, 6000.0, None])

    converted = plant_data._normalise_ncv(sparse, "f_k_coal_ncv")

    assert converted.notna().all()


@pytest.mark.parametrize("model_name", ["Linear regression", "Random forest"])
def test_when_training_then_results_are_shaped_for_charting(model_name: str):
    data = plant_data.load_example_data("abc")

    results = plant_data.train_and_score(data, model_name=model_name)

    assert {"timestamp", "month", "actual", "predicted", "error"} <= set(
        results.predictions.columns
    )
    assert len(results.feature_importances) == len(plant_data.fuel_columns(data)) + 1
    assert results.test_row_count > 0
    assert results.mean_absolute_error >= 0
    # A model that cannot beat guessing the mean is broken, not merely weak.
    assert results.r_squared > 0


def test_when_splitting_then_test_period_follows_training_period():
    """The split must be chronological, or the score is meaningless."""
    data = plant_data.load_example_data("abc")

    results = plant_data.train_and_score(data)

    train_row_count = results.train_row_count
    earliest_test_timestamp = results.predictions["timestamp"].min()
    latest_train_timestamp = data["timestamp"].iloc[train_row_count - 1]
    assert earliest_test_timestamp > latest_train_timestamp


def test_when_model_name_unknown_then_raises():
    data = plant_data.load_example_data("abc")

    with pytest.raises(ValueError, match="unknown model_name"):
        plant_data.train_and_score(data, model_name="crystal ball")


def test_when_summarising_by_month_then_one_row_per_month():
    data = plant_data.load_example_data("bcd")

    results = plant_data.train_and_score(data)

    monthly = results.monthly_errors
    assert monthly["month"].is_unique
    assert monthly["sample_count"].sum() == results.test_row_count


def test_results_are_immutable():
    """Tripwire: ModelResults must stay frozen."""
    data = plant_data.load_example_data("abc")
    results = plant_data.train_and_score(data)

    with pytest.raises(dataclasses.FrozenInstanceError):
        results.r_squared = 1.0  # type: ignore[misc]


def _example_predictions() -> pd.DataFrame:
    """A tiny in-memory predictions frame, built inline -- no fixture files."""
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2023-01-01", "2023-01-02", "2023-02-01", "2023-02-02"]
            ),
            "actual": [800.0, 820.0, 810.0, 830.0],
            "predicted": [805.0, 815.0, 800.0, 840.0],
        }
    )


def _example_importances() -> pd.DataFrame:
    return pd.DataFrame(
        {"feature": ["f_k_coal_tput", "s_ph_sil_tput"], "importance": [0.3, 0.7]}
    )


def test_when_given_in_memory_dataframes_then_builds_results():
    """The interface the student uses: DataFrames in, chartable results out."""
    results = plant_data.build_results(
        predictions=_example_predictions(),
        feature_importances=_example_importances(),
        train_row_count=16,
    )

    assert results.test_row_count == 4
    assert results.train_row_count == 16
    assert results.mean_absolute_error == pytest.approx(7.5)
    # month is derived for us, so the bar chart has something to group by.
    assert len(results.monthly_errors) == 2


def test_when_importances_unsorted_then_ordered_largest_first():
    results = plant_data.build_results(
        predictions=_example_predictions(),
        feature_importances=_example_importances(),
        train_row_count=16,
    )

    assert results.feature_importances["feature"].tolist() == [
        "s_ph_sil_tput",
        "f_k_coal_tput",
    ]


def test_when_building_results_then_callers_dataframe_not_mutated():
    """A function handed a DataFrame must not modify the caller's copy."""
    predictions = _example_predictions()

    plant_data.build_results(
        predictions=predictions,
        feature_importances=_example_importances(),
        train_row_count=16,
    )

    assert "error" not in predictions.columns
    assert "month" not in predictions.columns


def test_when_predictions_missing_a_column_then_raises_naming_it():
    incomplete = _example_predictions().drop(columns=["predicted"])

    with pytest.raises(ValueError, match=r"missing required column\(s\) \['predicted'\]"):
        plant_data.build_results(
            predictions=incomplete,
            feature_importances=_example_importances(),
            train_row_count=16,
        )


def test_when_importances_missing_a_column_then_raises_naming_it():
    incomplete = _example_importances().drop(columns=["importance"])

    with pytest.raises(ValueError, match=r"missing required column\(s\) \['importance'\]"):
        plant_data.build_results(
            predictions=_example_predictions(),
            feature_importances=incomplete,
            train_row_count=16,
        )


def test_when_predictions_empty_then_raises():
    empty = _example_predictions().iloc[0:0]

    with pytest.raises(ValueError, match="must not be empty"):
        plant_data.build_results(
            predictions=empty,
            feature_importances=_example_importances(),
            train_row_count=16,
        )


def test_when_month_column_supplied_then_kept():
    predictions = _example_predictions()
    predictions["month"] = pd.to_datetime("2023-01-01")

    results = plant_data.build_results(
        predictions=predictions,
        feature_importances=_example_importances(),
        train_row_count=16,
    )

    assert len(results.monthly_errors) == 1
