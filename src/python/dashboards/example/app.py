"""An example Streamlit dashboard, built to be read and played with.

Run it with:

    pants run src/python/dashboards:example

Every chart below comes with two notes: what it shows, and when you should
(and should not) reach for that chart type. Change things, break things, and
re-run -- Streamlit reloads as soon as you save the file.

How Streamlit works, in one paragraph: this file is a *script*, top to bottom.
Streamlit runs the whole thing again from the start every time you touch a
widget. That is why there are no callbacks or event handlers -- a slider just
returns its current value, and the code below it runs again with the new one.

The charts are drawn with **plotly**, via `plotly.express` (imported as `px`).
Every `px` call returns a `Figure`, which you can keep tweaking with
`update_traces` and `update_layout` before handing it to `st.plotly_chart`.
Charts are interactive for free: hover for values, drag to zoom, double-click
to reset.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.python.dashboards.example import plant_data

# A single accent colour for "predicted" and a neutral for "actual", used
# consistently in every chart. Picking the palette once, up here, is what
# makes a dashboard look deliberate rather than assembled.
ACTUAL_COLOUR = "#5A6B7B"
PREDICTED_COLOUR = "#E8833A"
GOOD_COLOUR = "#3E8E7E"

CHART_HEIGHT = 320

# Plotly's default template draws a grey backdrop and heavy gridlines. A light
# template with faint gridlines keeps the data as the most visible thing on
# the chart, which is the whole point.
CHART_TEMPLATE = "plotly_white"

st.set_page_config(page_title="SHC dashboard example", page_icon="🏭", layout="wide")


def _style(figure: go.Figure, y_title: str, x_title: str = "") -> go.Figure:
    """Apply the same layout to every chart on the page.

    Doing this in one place is what makes six charts look like one dashboard
    rather than six screenshots from different tools.
    """
    figure.update_layout(
        template=CHART_TEMPLATE,
        height=CHART_HEIGHT,
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        hovermode="x unified",
    )
    return figure


def main() -> None:
    st.title("🏭 Example dashboard: predicting SHC")
    st.markdown(
        "This is a **worked example** for Phase 3. It trains a model and shows "
        "the results six different ways. Read the notes under each chart -- they "
        "explain what the chart is for, not just what it says."
    )
    st.info(
        "**A dashboard does not load data or train models.** It is handed "
        "**DataFrames that already exist in memory** and just draws them. This "
        "example reads the sample CSVs only so it has something to show without "
        "your ClickHouse credentials -- that is the one piece you would swap for "
        "your own `data_load()`. See **Using your own DataFrames** at the bottom "
        "of the page for how to plug in what your training code already produces."
    )

    plant_ref, model_name = _sidebar_controls()

    data = plant_data.load_example_data(plant_ref)
    results = plant_data.train_and_score(data, model_name=model_name)

    _show_headline_metrics(results)

    st.divider()
    _show_time_series(data, results)
    st.divider()
    _show_scatter(results)
    st.divider()
    _show_monthly_errors(results)
    st.divider()
    _show_error_histogram(results)
    st.divider()
    _show_feature_importances(results)
    st.divider()
    _show_correlation_heatmap(data)
    st.divider()
    _show_chart_choosing_guide()
    st.divider()
    _show_using_your_own_dataframes()


def _sidebar_controls() -> tuple[str, str]:
    """Widgets that drive the whole page.

    Best practice: put controls in the sidebar. It keeps the charts as the
    thing people look at, and it stops the page shifting around as widgets
    change size.
    """
    with st.sidebar:
        st.header("Controls")
        plant_ref = st.selectbox(
            "Plant",
            options=list(plant_data.PLANTS),
            format_func=lambda ref: f"{ref.upper()} - {plant_data.PLANTS[ref]}",
        )
        model_name = st.radio("Model", options=["Random forest", "Linear regression"])
        st.caption(
            "Try the same plant with both models. The random forest usually wins "
            "here, but look at *where* each one is wrong, not just the score."
        )
    return plant_ref, model_name


def _show_headline_metrics(results: plant_data.ModelResults) -> None:
    """Big numbers at the top.

    `st.metric` is for the two or three numbers someone wants without
    reading a chart. Resist adding more -- ten metrics in a row is a table,
    and a table is easier to read as a table.
    """
    st.subheader("Headline numbers")
    first, second, third, fourth = st.columns(4)
    first.metric("Mean absolute error", f"{results.mean_absolute_error:.1f} kcal/kg")
    second.metric("RMSE", f"{results.root_mean_squared_error:.1f} kcal/kg")
    third.metric("R²", f"{results.r_squared:.3f}")
    fourth.metric("Test rows", f"{results.test_row_count:,}")

    _explain(
        shows=(
            "Three ways of saying 'how wrong is the model', plus how much data "
            "we tested on. **MAE** is the average miss in kcal/kg -- the easiest "
            "to explain to a plant engineer. **RMSE** punishes big misses harder, "
            "so if RMSE is much larger than MAE you have some bad outliers. "
            "**R²** is the fraction of the variation the model explains: 1.0 is "
            "perfect, 0 is no better than always guessing the average."
        ),
        practice=(
            "Always show the units. A metric reading '23.4' is useless; "
            "'23.4 kcal/kg' can be judged. And always show the sample size "
            "somewhere -- a brilliant score on 40 rows is luck, not skill."
        ),
    )


def _show_time_series(data: pd.DataFrame, results: plant_data.ModelResults) -> None:
    """Line chart: the classic for anything measured over time."""
    st.subheader("1. Line chart - actual vs predicted over time")

    predictions = results.predictions
    plotted = predictions.melt(
        id_vars="timestamp",
        value_vars=["actual", "predicted"],
        var_name="series",
        value_name="shc",
    )

    figure = px.line(
        plotted,
        x="timestamp",
        y="shc",
        color="series",
        # Naming the colours explicitly, rather than taking plotly's defaults,
        # keeps "actual" the same grey in every chart on the page.
        color_discrete_map={"actual": ACTUAL_COLOUR, "predicted": PREDICTED_COLOUR},
        labels={"shc": "SHC (kcal/kg)", "timestamp": "Time", "series": ""},
    )
    figure.update_traces(opacity=0.85, hovertemplate="%{y:.1f} kcal/kg")
    # Plotly does not force a zero baseline on a line chart, which is what we
    # want here: SHC sits around 800 kcal/kg, so a zero-based axis would
    # squash all the interesting variation into a thin band at the top.
    _style(figure, y_title="SHC (kcal/kg)", x_title="Time")
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "The held-out test period, with what actually happened in grey and "
            "what the model thought would happen in orange. Where the orange "
            "tracks the grey, the model is working. Where they part company, "
            "something happened that the model's inputs do not capture."
        ),
        practice=(
            "**Use a line chart when the x-axis is time** and the points are "
            "evenly spaced -- lines imply 'and it did something in between', "
            "which is true for a sensor reading and false for four separate "
            "plants. Two or three lines is readable; ten is spaghetti, so "
            "facet into small multiples instead. Do not force the y-axis to "
            "zero for a quantity that never goes near zero, and do not "
            "truncate the axis on a chart meant to show absolute size."
        ),
    )


def _show_scatter(results: plant_data.ModelResults) -> None:
    """Scatter plot: the standard way to judge a regression model."""
    st.subheader("2. Scatter plot - predicted vs actual")

    predictions = results.predictions
    lowest = float(min(predictions["actual"].min(), predictions["predicted"].min()))
    highest = float(max(predictions["actual"].max(), predictions["predicted"].max()))

    figure = px.scatter(
        predictions,
        x="actual",
        y="predicted",
        opacity=0.35,
        color_discrete_sequence=[PREDICTED_COLOUR],
        custom_data=["timestamp"],
    )
    figure.update_traces(
        marker=dict(size=7),
        hovertemplate=(
            "Actual %{x:.1f} kcal/kg<br>Predicted %{y:.1f} kcal/kg"
            "<br>%{customdata[0]|%Y-%m-%d %H:%M}<extra></extra>"
        ),
    )
    # A perfect model puts every point on this line, so it is the reference the
    # eye needs. A scatter of predictions without it is much harder to read.
    figure.add_shape(
        type="line",
        x0=lowest,
        y0=lowest,
        x1=highest,
        y1=highest,
        line=dict(color=ACTUAL_COLOUR, dash="dash", width=2),
    )
    _style(figure, y_title="Predicted SHC (kcal/kg)", x_title="Actual SHC (kcal/kg)")
    # Identical ranges on both axes, so the reference line sits at a true 45
    # degrees. Without this the eye is being lied to.
    figure.update_layout(
        xaxis_range=[lowest, highest],
        yaxis_range=[lowest, highest],
        hovermode="closest",
    )
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "One dot per test row. The dashed line is where a perfect "
            "prediction would land. Dots above the line are over-predictions, "
            "below are under-predictions. A model that is systematically "
            "biased shows up as a cloud sitting to one side of the line; a "
            "model that is merely noisy shows as a cloud centred on it."
        ),
        practice=(
            "**Use a scatter plot to compare two continuous quantities**, "
            "especially to test a relationship. Give both axes the *same* "
            "range when they measure the same thing -- otherwise the "
            "reference line is not at 45° and your eye is being lied to. "
            "With thousands of points, turn the opacity down so density "
            "becomes visible instead of one solid blob."
        ),
    )


def _show_monthly_errors(results: plant_data.ModelResults) -> None:
    """Bar chart: comparing a value across distinct categories."""
    st.subheader("3. Bar chart - error by month")

    monthly = results.monthly_errors
    if len(monthly) < 2:
        st.info(
            "This plant's test split lands inside a single month, so there is "
            "only one bar. Pick a plant with more data to see this chart work."
        )
        return

    figure = px.bar(
        monthly,
        x="month",
        y="mae",
        color_discrete_sequence=[PREDICTED_COLOUR],
        custom_data=["sample_count"],
    )
    figure.update_traces(
        hovertemplate=(
            "%{x|%b %Y}<br>MAE %{y:.1f} kcal/kg<br>%{customdata[0]:,} rows<extra></extra>"
        )
    )
    _style(figure, y_title="MAE (kcal/kg)", x_title="Month")
    # Bars must start at zero. Their length is the message, and a truncated
    # axis makes small differences look enormous. Plotly does this by default
    # for bars, but say it explicitly so nobody "tidies" it away later.
    figure.update_layout(yaxis_rangemode="tozero")
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "How the average miss changes month to month. This is the chart "
            "`main.py` is building towards. A month that sticks out is worth "
            "investigating: usually the plant did something unusual, or a "
            "sensor drifted, and the model had never seen it before."
        ),
        practice=(
            "**Use bars to compare a number across categories**, and "
            "**always start the bar axis at zero** -- this is the one axis "
            "rule with no exceptions, because a bar encodes its value as "
            "length. Sort bars by value when the categories have no natural "
            "order; keep chronological order when they do, as here. Check the "
            "row count per bar before believing it: a month with 20 rows will "
            "bounce around for reasons that have nothing to do with the model."
        ),
    )


def _show_error_histogram(results: plant_data.ModelResults) -> None:
    """Histogram: the shape of a single variable's distribution."""
    st.subheader("4. Histogram - distribution of errors")

    bin_count = st.slider("Number of bins", min_value=10, max_value=80, value=40)

    figure = px.histogram(
        results.predictions,
        x="error",
        nbins=bin_count,
        color_discrete_sequence=[PREDICTED_COLOUR],
        opacity=0.85,
    )
    figure.update_traces(hovertemplate="Error %{x:.0f} kcal/kg<br>%{y} rows<extra></extra>")
    _style(
        figure,
        y_title="Number of rows",
        x_title="Prediction error (kcal/kg)  -  negative = under-predicted",
    )
    # A line at zero error: without it, a distribution sitting slightly off
    # centre looks centred.
    figure.add_vline(x=0, line=dict(color=ACTUAL_COLOUR, dash="dash", width=2))
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "How the errors are spread out. What you want is a single hump "
            "centred on zero: the model is usually right, and its mistakes go "
            "both ways. A hump centred left or right of zero means systematic "
            "bias, which is good news -- bias is fixable. Two humps usually "
            "means the plant runs in two distinct modes and the model has "
            "averaged them into one compromise."
        ),
        practice=(
            "**Use a histogram to see the shape of one variable** -- averages "
            "hide everything interesting, and two datasets with identical "
            "means can look completely different here. Drag the bin slider: "
            "too few bins hides real structure, too many turns the "
            "distribution into noise. Bin count is a genuine analytical "
            "choice, so try several before drawing a conclusion from any one."
        ),
    )


def _show_feature_importances(results: plant_data.ModelResults) -> None:
    """Horizontal bar chart: ranked categories with long labels."""
    st.subheader("5. Horizontal bar chart - what the model relies on")

    figure = px.bar(
        results.feature_importances,
        x="importance",
        # Horizontal because feature names are long. Rotated labels on a
        # vertical chart are a reliable sign the chart wanted to be horizontal
        # all along.
        y="feature",
        orientation="h",
        color_discrete_sequence=[GOOD_COLOUR],
    )
    figure.update_traces(hovertemplate="%{y}<br>Importance %{x:.3f}<extra></extra>")
    _style(figure, y_title="", x_title="Relative importance")
    figure.update_layout(
        height=max(CHART_HEIGHT - 100, 40 * len(results.feature_importances)),
        # build_results sorts largest-first, but plotly draws the first row at
        # the bottom of a horizontal bar chart. Reversing the axis puts the
        # biggest bar on top, where the eye starts.
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "Which inputs the model leans on most. For the random forest this "
            "is how much each feature reduced prediction error; for the linear "
            "model it is the size of each coefficient. Either way it is a "
            "sanity check: fuel throughput and calorific value *should* "
            "dominate an SHC model. If something irrelevant tops this chart, "
            "you probably have a leak or a bug rather than an insight."
        ),
        practice=(
            "**Go horizontal when labels are long**, and **sort by value** so "
            "the ranking is instant (sorted upstream, then the y-axis is "
            "reversed so the biggest bar sits on top). Importance is "
            "about correlation, not causation -- it tells you what the model "
            "used, not what drives the plant. Two features that measure nearly "
            "the same thing will split their importance between them and both "
            "look weaker than they are."
        ),
    )


def _show_correlation_heatmap(data: pd.DataFrame) -> None:
    """Heatmap: one value for every pair in a grid."""
    st.subheader("6. Heatmap - how the inputs relate to each other")

    columns = plant_data.fuel_columns(data) + ["s_ph_sil_tput", plant_data.TARGET]
    correlations = data[columns].corr()

    figure = px.imshow(
        correlations,
        # Diverging scale anchored at 0: correlation runs -1..+1 and the sign
        # matters, so the midpoint must be visually neutral. zmin/zmax pin the
        # ends, otherwise plotly scales to whatever range this plant happens
        # to have and the colours mean something different per plant.
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        # A heatmap shows patterns well and precise values badly, so print the
        # number in each cell as well.
        text_auto=".2f",
        aspect="auto",
    )
    figure.update_traces(hovertemplate="%{y}<br>vs %{x}<br>Correlation %{z:.2f}<extra></extra>")
    _style(figure, y_title="", x_title="")
    figure.update_layout(coloraxis_colorbar_title="Correlation")
    st.plotly_chart(figure, use_container_width=True)

    _explain(
        shows=(
            "How strongly every pair of columns moves together. +1 means they "
            "rise and fall in lockstep, -1 means one rises as the other falls, "
            "0 means no linear relationship. Read the `shc` row to see which "
            "inputs relate most directly to what you are predicting."
        ),
        practice=(
            "**Use a heatmap for one value across two categorical axes**, "
            "particularly a correlation matrix. Use a **diverging** colour "
            "scale whenever zero is meaningful, and centre it on zero -- a "
            "sequential scale here would make -0.9 and 0.0 look equally "
            "unremarkable. Keep it under roughly 15×15: beyond that nobody "
            "can find the cell they want. Heatmaps show *patterns* well and "
            "*precise values* badly, so put the number in the tooltip."
        ),
    )


def _show_chart_choosing_guide() -> None:
    """A cheat sheet, and the traps worth knowing about."""
    st.subheader("Choosing a chart")
    st.markdown(
        "The question comes first, then the chart. Pick the chart that answers "
        "the question you actually have:"
    )
    st.dataframe(
        pd.DataFrame(
            [
                (
                    "How has it changed over time?",
                    "Line chart",
                    "Time on x, one line per series",
                ),
                ("How do these groups compare?", "Bar chart", "Zero baseline, sorted by value"),
                ("Are these two things related?", "Scatter plot", "Add a reference line"),
                ("What does the spread look like?", "Histogram", "Try several bin counts"),
                ("Which of many is biggest?", "Horizontal bars", "Long labels stay readable"),
                ("What is the pattern across pairs?", "Heatmap", "Diverging scale, centred"),
                ("What is the single headline?", "A big number", "`st.metric`, with units"),
            ],
            columns=["Your question", "Chart", "Key detail"],
        ),
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("Traps that catch everyone at least once"):
        st.markdown(
            "- **Pie charts.** People compare angles badly. Two or three slices "
            "is survivable; past that a sorted bar chart is strictly better.\n"
            "- **Truncated bar axes.** Starting a bar chart at 900 instead of 0 "
            "turns a 2% difference into a visual landslide. Bars encode length, "
            "so the baseline must be zero.\n"
            "- **Dual y-axes.** Two different scales on one chart lets you "
            "manufacture any correlation you like by sliding the axes. Use two "
            "stacked charts sharing an x-axis instead.\n"
            "- **Red/green as the only signal.** Roughly 1 in 12 men cannot "
            "reliably separate them. Vary shape, position or label too.\n"
            "- **No units, no sample size.** '23.4' and 'R²=0.99' both mean "
            "nothing on their own. Say what the units are and how many rows "
            "it was measured on.\n"
            "- **A chart with no takeaway.** If you cannot say in one sentence "
            "what a chart is for, it is decoration. Delete it -- every extra "
            "chart makes the important ones harder to find."
        )

    st.info(
        "**Your turn.** Some things to try: add a rolling 24-hour average line "
        "to chart 1; colour the scatter points by month to see if accuracy "
        "drifts; make chart 3 show RMSE next to MAE; add a date-range filter to "
        "the sidebar. Everything you need is in this file and `plant_data.py`."
    )


def _show_using_your_own_dataframes() -> None:
    """How to point this dashboard at the student's own training output."""
    st.subheader("Using your own DataFrames")
    st.markdown(
        "Every chart above was drawn from **plain pandas DataFrames held in "
        "memory** -- nothing was saved to disk and re-read. That is the whole "
        "trick, and it means your own training run can feed this dashboard "
        "without changing any of the charting code."
    )

    st.markdown("**The two DataFrames the charts need**")
    first, second = st.columns(2)
    with first:
        st.markdown("`predictions` — one row per test sample")
        st.dataframe(
            pd.DataFrame(
                [
                    ("timestamp", "datetime", "when the reading was taken"),
                    ("actual", "float", "the measured value"),
                    ("predicted", "float", "what your model said"),
                ],
                columns=["Column", "Type", "Meaning"],
            ),
            hide_index=True,
            use_container_width=True,
        )
    with second:
        st.markdown("`feature_importances` — one row per input")
        st.dataframe(
            pd.DataFrame(
                [
                    ("feature", "str", "the feature's name"),
                    ("importance", "float", "how much the model leans on it"),
                ],
                columns=["Column", "Type", "Meaning"],
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.markdown(
        "Hand those to `build_results` and it works out the rest -- the error "
        "column, the monthly summary, MAE, RMSE and R². Your training loop in "
        "`main.py` already has every piece it needs:"
    )
    st.code(
        """import pandas as pd
import streamlit as st

from src.python.dashboards.example import plant_data

# ---- your existing code, unchanged ----
data = data_load()              # or pd.read_csv, or anything else
data = cleaning(data)
model, x_test, y_test = train_model(data)
predicted = model.predict(x_test)

# ---- the handoff: in-memory DataFrames, no files ----
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
    train_row_count=len(data) - len(x_test),
)

# ---- now draw it ----
st.metric("MAE", f"{results.mean_absolute_error:.1f} kcal/kg")
st.dataframe(results.monthly_errors)""",
        language="python",
    )

    _explain(
        shows=(
            "The join between your work and this dashboard. `build_results` "
            "takes DataFrames, validates that they have the columns the charts "
            "need, and raises a clear error naming the missing column if they "
            "do not -- so a typo fails immediately instead of producing an "
            "empty chart you have to debug."
        ),
        practice=(
            "**Keep loading, training and drawing in separate functions.** A "
            "dashboard that trains its own model has to retrain every time "
            "anyone touches a widget, because Streamlit re-runs the whole "
            "script each time -- so it feels broken. Pass DataFrames in "
            "instead, and if a step genuinely is slow, cache it with "
            "`@st.cache_data` so it runs once and is reused on every re-run."
        ),
    )

    with st.expander("Why in-memory, and not a CSV in between?"):
        st.markdown(
            "- **Nothing to keep in sync.** A CSV on disk is a copy that goes "
            "stale the moment you retrain. A DataFrame in memory is the "
            "result, not a snapshot of it.\n"
            "- **No schema drift.** Writing and re-reading a CSV loses dtypes "
            "-- timestamps come back as strings, and your time axis silently "
            "sorts as text.\n"
            "- **It is faster.** Serialising a year of minute data to disk and "
            "parsing it back costs far more than passing a reference.\n"
            "- **It composes.** A function that takes and returns DataFrames "
            "can be tested with a three-row DataFrame built inline, with no "
            "fixture files at all -- see `plant_data_test.py`.\n\n"
            "Files earn their place when data must outlive the process (a "
            "trained model you will load tomorrow) or cross a machine "
            "boundary. Between two functions in one script, pass the object."
        )


def _explain(shows: str, practice: str) -> None:
    """Render the two teaching notes that accompany every chart."""
    first, second = st.columns(2)
    with first:
        st.markdown(f"**What this shows**\n\n{shows}")
    with second:
        st.markdown(f"**When to use it / what to watch for**\n\n{practice}")


main()
