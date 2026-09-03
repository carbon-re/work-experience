"""Macro for running Streamlit dashboards with pants.

Adapted from the carbo monorepo. Lets a BUILD file declare a dashboard in one
line:

    streamlit_dashboard(name="example", entrypoint="example/app.py")

and the student runs it with:

    pants run src/python/dashboards:example
"""


def streamlit_dashboard(name, entrypoint, root=None, extra_deps=None):
    """Define a runnable Streamlit app.

    Args:
        name: target name, used as `pants run <dir>:<name>`.
        entrypoint: path to the app's .py file, relative to the BUILD file.
        root: directory the entrypoint is relative to. Defaults to the
            directory holding the BUILD file.
        extra_deps: any additional pants targets the app needs, e.g. a
            `resources()` target holding CSV files.
    """
    root = root or build_file_dir()  # noqa: F821 - injected by pants prelude
    extra_deps = extra_deps or []
    pex_binary(  # noqa: F821 - injected by pants prelude
        name=name,
        script="streamlit",
        args=["run", f"{root}/{entrypoint}"],
        execution_mode="venv",
        layout="packed",
        dependencies=[f"{root}/{entrypoint}", *extra_deps],
    )
