"""Kim's SHC dashboard, laid out for someone reading it for the first time.

Same model and same charts as `app.py`. What changed is the order and the
words:

* the scores come **first**, because that is what a reader wants to know;
* every number and every chart has a plain-English note under it;
* the two charts sit side by side instead of stacked;
* the date range and the train/test split are controls, not constants.

Run it with `pants run src/python:yakyms_dashboard_v2`.
"""

import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.python.main import (
    DEFAULT_END,
    DEFAULT_START,
    analysisData,
    cleaning,
    data_load,
    features,
    sliced_data,
    train_model,
)

# Kept narrow on purpose: two charts side by side in half-width columns need
# to be readable, not detailed.
CHART_FIGSIZE = (7, 4)
ACTUAL_COLOUR = "#5A6B7B"
PREDICTED_COLOUR = "#E8833A"

# The sensor names in the database are short and cryptic. These are the same
# readings in words, so the picker means something to someone who has never
# seen a cement plant.
FEATURE_LABELS = {
    "f_k_coal_tput": "Coal going into the kiln",
    "p_k_torque": "How hard the kiln motor is working",
    "g_k_pyro_temp": "Temperature inside the kiln",
    "p_c_grate_speed": "Speed of the cooler grate",
    "g_ph_cy4_gol_temp": "Preheater temperature (cyclone 4)",
    "g_ph_cy3_gol_temp": "Preheater temperature (cyclone 3)",
}


def describe_feature(name: str) -> str:
    """Friendly name for a sensor, falling back to the raw one."""
    return FEATURE_LABELS.get(name, name)


st.set_page_config(
    page_title="Predicting a cement plant's energy use",
    page_icon="🏭",
    layout="wide",
)


# ----------------------------------------------------------------------
# Loading and training
#
# Both are cached. Streamlit re-runs this whole file top to bottom every
# time a control moves, and training happens thirteen times per render
# (one model per month, plus one for the whole period). Without the cache,
# nudging the slider would refit all thirteen and the page would feel
# broken.
# ----------------------------------------------------------------------


@st.cache_data(show_spinner="Loading plant data…")
def load_plant_data(start: dt.datetime, end: dt.datetime) -> pd.DataFrame:
    data = data_load(start=start, end=end)
    return cleaning(data)


@st.cache_data(show_spinner="Training a model for each month…")
def train_monthly_models(
    data: pd.DataFrame, test_size: float, selected_features: list[str]
) -> tuple[list, list]:
    """One model per calendar month, so we can see error drift over the year."""
    months = []
    maes = []

    for month_df in sliced_data(data.copy()):
        model, x_test, y_test = train_model(
            month_df, test_size=test_size, selected_features=selected_features
        )
        _, mae = analysisData(x_test, y_test, model=model)
        months.append(month_df["month"].iloc[0].to_timestamp())
        maes.append(mae)

    return months, maes


@st.cache_data(show_spinner="Training the overall model…")
def train_overall_model(
    data: pd.DataFrame, test_size: float, selected_features: list[str]
) -> tuple[pd.Series, pd.Series]:
    """One model across the whole period, for the actual-vs-predicted line."""
    model, x_test, y_test = train_model(
        data, test_size=test_size, selected_features=selected_features
    )
    predictions, _ = analysisData(x_test, y_test, model=model)
    return y_test, predictions


def calculate_metrics(actuals, predictions) -> tuple[float, float, float]:
    r2 = r2_score(actuals, predictions)
    mae = mean_absolute_error(actuals, predictions)
    rmse = mean_squared_error(actuals, predictions) ** 0.5

    return r2, mae, rmse


# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------


def plot_scatter(a, b, a_label, b_label, alpha=0.8, color=PREDICTED_COLOUR):
    fig, ax = plt.subplots(figsize=CHART_FIGSIZE)
    ax.scatter(a, b, alpha=alpha, color=color)
    ax.set_xlabel(a_label)
    ax.set_ylabel(b_label)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    st.pyplot(fig)


def plot_line(actuals, predictions):
    actuals = list(actuals)
    predictions = list(predictions)

    if len(actuals) != len(predictions):
        st.error(
            f"Actuals and predictions have different lengths: "
            f"{len(actuals)} vs {len(predictions)}"
        )
        return

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE)
    x = range(len(actuals))
    ax.plot(x, actuals, label="What really happened", color=ACTUAL_COLOUR, linewidth=1)
    ax.plot(x, predictions, label="What the model guessed", color=PREDICTED_COLOUR, linewidth=1)
    ax.set_xlabel("Test reading (in time order)")
    ax.set_ylabel("Energy use (kcal/kg)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)


# ----------------------------------------------------------------------
# Page sections
# ----------------------------------------------------------------------


def show_header_and_controls() -> tuple[dt.date, dt.date, float, list[str]]:
    """Title on the left, the controls boxed off in the top-right corner."""
    heading, controls = st.columns([2, 1])

    with heading:
        st.title("🏭 Predicting a cement plant's energy use")
        st.markdown(
            "Making cement takes a **lot** of heat. This page measures how much "
            "energy the plant uses for every kilogram of cement it makes — that "
            "number is called **SHC**, and a lower one means less fuel burnt and "
            "less CO₂."
        )
        st.markdown(
            "A computer model tries to predict SHC from sensor readings around "
            "the plant, such as how fast coal is going in and how hot the kiln "
            "is. Everything below asks the same question: **can we trust it?**"
        )

    with controls:
        with st.container(border=True):
            st.markdown("### ⚙️ Options")
            st.caption("Change these and the page works itself out again.")

            start_date, end_date = st.date_input(
                "Which dates should we look at?",
                value=(DEFAULT_START.date(), DEFAULT_END.date()),
                format="YYYY-MM-DD",
            ) or (None, None)

            selected_features = st.multiselect(
                "Which sensor readings can the model use?",
                options=features,
                default=features,
                format_func=describe_feature,
            )
            st.caption(
                "These are the clues the model is allowed to look at. Take some "
                "away and see whether it can still do the job — if the scores "
                "barely move, that reading was not telling it much."
            )

            test_percent = st.slider(
                "How much data to hide from the model, for testing",
                min_value=10,
                max_value=40,
                value=20,
                step=5,
                format="%d%%",
            )
            st.caption(
                "The model never sees this part while it learns, so we can "
                "check its guesses against readings it has never met."
            )

    return start_date, end_date, test_percent / 100, selected_features


def show_metrics(r2: float, mae: float, rmse: float) -> None:
    """The scores, first on the page, each with an explanation underneath."""
    st.subheader("How good is the model?")

    first, second, third = st.columns(3)

    with first:
        st.metric("R² — how much it explains", f"{r2:.2f}")
        st.markdown(
            "Out of everything that makes the plant's energy use go up and "
            "down, this is the **share the model can explain**. "
            "`1.00` would be perfect. `0.00` means it is no better than always "
            "guessing the average."
        )

    with second:
        st.metric("MAE — the typical miss", f"{mae:.1f} kcal/kg")
        st.markdown(
            "On average, this is **how far off each guess is**. If MAE is "
            "20 kcal/kg, a typical prediction is about 20 either side of the "
            "real answer. Smaller is better."
        )

    with third:
        st.metric("RMSE — the miss, punishing howlers", f"{rmse:.1f} kcal/kg")
        st.markdown(
            "Like MAE, but **big mistakes count for much more**. If this is a "
            "lot bigger than MAE, the model is usually fine but occasionally "
            "very wrong — worth knowing before anyone relies on it."
        )


def show_charts(months, maes, actuals, predictions) -> None:
    """Scatter on the left, line on the right, a note under each."""
    left, right = st.columns(2)

    with left:
        st.subheader("Is it worse in some months?")
        plot_scatter(months, maes, "Month", "Typical miss (kcal/kg)")
        st.markdown(
            "**What this shows.** One dot per month, showing how far off the "
            "model typically was that month. A flat line of dots means it "
            "copes all year round. A dot that jumps up is a month where "
            "something happened the sensors do not explain — a shutdown, a "
            "change of fuel, or a broken instrument."
        )

    with right:
        st.subheader("Guesses vs what really happened")
        plot_line(actuals, predictions)
        st.markdown(
            "**What this shows.** The grey line is the plant's real energy "
            "use; the orange line is what the model thought it would be. "
            "Where orange sits on top of grey, the model is working. Where "
            "they drift apart, it is missing something. This only covers the "
            "hidden test data, so these are genuine guesses, not memories."
        )


def main() -> None:
    start_date, end_date, test_size, selected_features = show_header_and_controls()

    if start_date is None or end_date is None:
        st.info("Pick a start date and an end date to get going.")
        return

    if not selected_features:
        st.warning(
            "The model needs at least one sensor reading to work from. Tick a "
            "box under **Which sensor readings can the model use?** to carry on."
        )
        return

    if start_date >= end_date:
        st.error(
            f"The start date ({start_date}) needs to come before the end date "
            f"({end_date}). Try widening the range."
        )
        return

    try:
        data = load_plant_data(
            dt.datetime.combine(start_date, dt.time.min),
            dt.datetime.combine(end_date, dt.time.min),
        )
    except ValueError as error:
        st.error(
            "Could not load the plant data, so there is nothing to show yet.\n\n"
            f"**What went wrong:** {error}\n\n"
            "This usually means the ClickHouse login details are not set. In "
            "your terminal, export `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, "
            "`CLICKHOUSE_PASSWORD` and `CLICKHOUSE_DATABASE`, then reload."
        )
        return

    if data.empty:
        st.warning(
            "No readings came back for those dates. Try a wider range — the "
            "sample data covers 2022."
        )
        return

    actuals, predictions = train_overall_model(data, test_size, selected_features)
    r2, mae, rmse = calculate_metrics(actuals, predictions)

    show_metrics(r2, mae, rmse)

    st.divider()

    months, maes = train_monthly_models(data, test_size, selected_features)
    show_charts(months, maes, actuals, predictions)

    st.divider()
    st.caption(
        f"Trained on readings from {start_date} to {end_date}, using "
        f"{len(selected_features)} of {len(features)} sensor readings "
        f"({', '.join(describe_feature(f).lower() for f in selected_features)}). "
        f"{len(actuals):,} readings were held back for testing "
        f"({test_size:.0%} of the data)."
    )


main()
