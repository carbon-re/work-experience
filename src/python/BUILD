python_sources()

# conftest.py holds the shared `test_data` fixture. Pants does not pick it up
# via python_sources(), so it gets its own target that tests depend on.
python_test_utils(name="test_utils")

streamlit_dashboard(name="yakyms_dashboard", entrypoint="app.py")
