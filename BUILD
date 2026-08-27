# Root BUILD file. Source root is the repo root, so imports are
# `from src.python...`, matching the existing code.

# Start Jupyter Lab with `pants run //:jupyter`.
pex_binary(
    name="jupyter",
    script="jupyter-lab",
    dependencies=["3rdparty/python:reqs#jupyterlab", "3rdparty/python:reqs#jupytext"],
)
