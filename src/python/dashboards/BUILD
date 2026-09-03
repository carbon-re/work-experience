python_sources()

# Run with `pants run src/python/dashboards:example`.
streamlit_dashboard(
    name="example",
    entrypoint="example/app.py",
    extra_deps=["src/infra/plant-data:csvs"],
)
