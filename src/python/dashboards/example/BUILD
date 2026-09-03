python_sources()

python_tests(
    name="tests",
    dependencies=[
        "src/infra/plant-data:csvs",
        # app_test.py runs app.py as a script rather than importing it, so
        # pants cannot infer this dependency. Without it, app.py is absent
        # from the test sandbox.
        ":example",
    ],
)
