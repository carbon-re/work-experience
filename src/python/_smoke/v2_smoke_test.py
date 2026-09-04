"""Temporary scaffolding: drive app_v2.py and report its widget tree."""
import pathlib

from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).parent.parent / "app_v2.py")


def test_page_renders():
    app = AppTest.from_file(APP, default_timeout=180)
    app.run()

    print("\n--- exception? ->", bool(app.exception))
    for e in app.exception:
        print("   EXC:", str(e.value)[:300])

    print("titles:", [t.value for t in app.title])
    print("date_input count:", len(app.date_input))
    print("multiselect count:", len(app.multiselect))
    for m in app.multiselect:
        print("   label:", m.label)
        print("   options:", m.options)
        print("   default:", m.value)
    print("slider count:", len(app.slider))
    print("error blocks:", [e.value[:150].replace("\n", " ") for e in app.error])
    print("warning blocks:", [w.value[:150].replace("\n", " ") for w in app.warning])

    assert not app.exception, "page raised"


def test_empty_feature_selection_warns():
    app = AppTest.from_file(APP, default_timeout=180)
    app.run()
    app.multiselect[0].set_value([]).run()

    print("\n--- after clearing features ---")
    print("exception? ->", bool(app.exception))
    print("warnings:", [w.value[:160].replace("\n", " ") for w in app.warning])

    assert not app.exception, "clearing features raised"
