"""Smoke test: the dashboard renders for every plant and model.

Importing `app.py` runs the whole Streamlit script, because that is how
Streamlit works -- the module body *is* the page. Running it here under
`streamlit.testing` catches the errors that a plain import would not: a bad
plotly figure spec, a column that only exists for some plants, a chart that
breaks when a plant's test split lands inside one month.
"""

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from src.python.dashboards.example import plant_data

# AppTest resolves a relative path against this test file's directory, so
# build an absolute one instead.
APP_PATH = str(pathlib.Path(__file__).parent / "app.py")
RENDER_TIMEOUT_SECONDS = 120


def _run_app(plant_ref: str | None = None, model_name: str | None = None) -> AppTest:
    app = AppTest.from_file(APP_PATH, default_timeout=RENDER_TIMEOUT_SECONDS)
    app.run()
    if plant_ref is not None:
        app.selectbox[0].set_value(plant_ref).run()
    if model_name is not None:
        app.radio[0].set_value(model_name).run()
    return app


def test_when_dashboard_runs_then_no_exception():
    app = _run_app()

    assert not app.exception


@pytest.mark.parametrize("plant_ref", sorted(plant_data.PLANTS))
def test_when_switching_plant_then_every_chart_renders(plant_ref: str):
    """Each plant has different fuel columns, so each exercises new code."""
    app = _run_app(plant_ref=plant_ref)

    assert not app.exception


def test_when_switching_model_then_no_exception():
    """The linear model takes a different importance path to the forest."""
    app = _run_app(model_name="Linear regression")

    assert not app.exception


def test_when_dashboard_runs_then_shows_all_six_charts_and_the_guide():
    app = _run_app()

    headings = [heading.value for heading in app.subheader]
    assert any("Line chart" in heading for heading in headings)
    assert any("Scatter plot" in heading for heading in headings)
    assert any("Bar chart" in heading for heading in headings)
    assert any("Histogram" in heading for heading in headings)
    assert any("Horizontal bar chart" in heading for heading in headings)
    assert any("Heatmap" in heading for heading in headings)
    assert any("Choosing a chart" in heading for heading in headings)
    # The in-memory DataFrame explanation the student needs in order to wire
    # their own training output in.
    assert any("Using your own DataFrames" in heading for heading in headings)


def test_when_dashboard_runs_then_headline_metrics_carry_units():
    app = _run_app()

    metric_values = [metric.value for metric in app.metric]
    assert any("kcal/kg" in value for value in metric_values)


def test_when_dashboard_runs_then_draws_six_plotly_charts():
    """Tripwire: all six charts must be plotly figures, not another library.

    `AppTest` has no typed `plotly_chart` accessor, so go via `get()`, which
    looks the elements up by their proto name.
    """
    app = _run_app()

    assert len(list(app.get("plotly_chart"))) == 6
