# Work Experience Repo

Welcome to your project!

This week you will build a machine learning model that predicts a cement plant's
**specific heat consumption** (SHC), then show the predictions in a dashboard.

SHC is the energy used to make one unit of clinker. If a plant makes 1 ton
(1000 kg) of clinker using 1,000,000 kcal of energy, its SHC is 1000 kcal/kg.
Lower is better: less fuel burnt means less CO2.

At the end of the week there is a short review session where you talk through
what you built. See [REVIEWME.md](REVIEWME.md) to prepare for it.

## The plan

| Phase | Goal                                                     |
| ----- | -------------------------------------------------------- |
| 1     | **Load** plant sensor data from ClickHouse                |
| 2     | **Train** an SHC soft sensor with scikit-learn            |
| 3     | **Predict & visualise** the results in a dashboard        |
| 4     | *Stretch*: deploy the model to run on a schedule          |

## Setting up your machine

Do this once, before day 1. Work through it in order — each step needs the
one before it.

### Step 1: Install git

Git is the tool we use to track changes to code. You need it before you can
download this repo.

**Mac** — install [Homebrew](https://brew.sh). It installs git for you along
the way. Everything else you need comes from the `Brewfile` in Step 4.

**Ubuntu** — open a terminal and run:

```bash
sudo apt-get update
sudo apt-get install git curl
```

Check it worked:

```bash
git --version
```

### Step 2: Authenticate with git

Your name goes on every change you make, so set it now:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 3: Download the repo

```bash
git clone https://github.com/carbon-re/work-experience
cd work-experience
```

Everything from here on is run **inside** the `work-experience` folder.

### Step 4: Install the rest of the tools

**Mac** — you already have Homebrew from Step 1, so just run:

```bash
brew bundle install
```

That reads the `Brewfile` and installs pyenv, Pants and node.

**Ubuntu** — install the build tools Python needs:

```bash
sudo apt-get install make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev tk-dev
```

Then pyenv, Pants and node:

```bash
curl -fsSL https://pyenv.run | bash
curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
sudo apt-get install nodejs npm
```

pyenv prints some lines to add to your shell config file when it finishes.
**Read that output and follow it**, then restart your terminal.

### Step 5: Install Python 3.11

We use [pyenv](https://github.com/pyenv/pyenv) so this project gets its own
Python, separate from the one your system uses.

```bash
pyenv install 3.11
pyenv local 3.11
```

Check it worked — this should print a 3.11 version:

```bash
python --version
```

### Step 6: Install Claude Code

Claude Code is an AI assistant that runs in your terminal.

```bash
npm install -g @anthropic-ai/claude-code
```

Then run `claude` inside the repo and follow the login prompts.

## Testing pants tools

Pants is our build tool. It installs Python packages for you, so you never
need `pip install`.

```bash
pants test ::          # run all the tests
pants lint ::          # check code style
pants fmt ::           # auto-format your code
pants green            # all of the above, before you commit
```

The first run downloads everything and takes a few minutes. After that it is
fast.

## Notebooks

Notebooks are good for exploring data and trying things out. Start one with:

```bash
pants run //:jupyter
```

That opens Jupyter Lab in your browser.

There is a starter notebook for Phase 2 at
`src/python/soft_sensor/notebook.ipynb`. Work through the `TODO`s in it.

Notebooks are for exploring & experimenting! Once code works, move it into
`src/python/` where it can be properly tested.

One thing to know: `.ipynb` files are stored as JSON, so git changes to them
are hard to read. Before committing, use *Kernel -> Restart Kernel and Clear
Outputs of All Cells* to keep the changes smaller.

## Dashboards

A dashboard is how you show your model's results to someone else. We use
[Streamlit](https://streamlit.io): you write normal Python, and it becomes a
web page.

There is a fully worked example to read and play with:

```bash
pants run src/python/dashboards:example
```

That opens a page with six kinds of chart -- line, scatter, bar, histogram,
horizontal bar and heatmap. Each one has a note explaining **what it shows**
and **when to use it**, plus a section on the traps (truncated bar axes, dual
y-axes, pie charts) that catch everyone at least once.

Change something in `src/python/dashboards/example/app.py`, save, and the page
reloads. That is the fastest way to learn what each chart setting does.

### Plugging in your own model

The dashboard does **not** load data or train models. It is handed **pandas
DataFrames that already exist in memory** and just draws them. Your training
code keeps ownership of loading and fitting; the dashboard only draws.

So once your model works, you do not rewrite the charts. You build two
DataFrames and pass them to `build_results`:

| DataFrame             | Columns                          |
| --------------------- | -------------------------------- |
| `predictions`         | `timestamp`, `actual`, `predicted` |
| `feature_importances` | `feature`, `importance`          |

```python
import pandas as pd
from src.python.dashboards.example import plant_data

model, x_test, y_test = train_model(data)   # your existing code

results = plant_data.build_results(
    predictions=pd.DataFrame(
        {
            "timestamp": data.loc[x_test.index, "timestamp"],
            "actual": y_test,
            "predicted": model.predict(x_test),
        }
    ),
    feature_importances=pd.DataFrame(
        {"feature": features, "importance": abs(model.coef_)}
    ),
    train_row_count=len(data) - len(x_test),
)
```

`build_results` works out the rest -- the error column, the per-month summary,
MAE, RMSE and R². Nothing is written to disk. The "Using your own DataFrames"
section at the bottom of the example page explains why that matters.

The example reads the sample CSVs in `src/infra/plant-data/` only so it has
something to show without ClickHouse credentials. That is the one piece you
would replace with your own `data_load()`.

### Adding your own dashboard

Make a directory with an `app.py`, then add to its `BUILD` file:

```python
streamlit_dashboard(name="my_dashboard", entrypoint="my_dashboard/app.py")
```

`streamlit_dashboard` is our own macro (in `pants-plugins/macros/`), which is
why `pants run` knows how to start a Streamlit app. Run it with
`pants run src/python/dashboards:my_dashboard`.

## Running the dashboard on Windows

Pants does not run on Windows, but the dashboard does not need it. You can run
`app_v2.py` with plain Python and pip.

You need **no passwords and no internet connection** for this — the plant data
is generated on your machine (see [Where the data comes from](#where-the-data-comes-from)
below).

### One-time setup

**Step 1 — install Python.** Get it from
[python.org/downloads](https://www.python.org/downloads/) and pick Python 3.11
or newer. On the first screen of the installer, tick **"Add python.exe to
PATH"** before clicking Install. That box is easy to miss and everything else
fails without it.

Open a new PowerShell window and check it worked:

```powershell
python --version
```

If that prints a version number, you are good. If Windows opens the Microsoft
Store instead, the PATH box was not ticked — re-run the installer and choose
"Modify".

**Step 2 — get the code.** If you have git:

```powershell
git clone https://github.com/carbon-re/work-experience
cd work-experience
```

No git? Download the ZIP from the GitHub page ("Code" → "Download ZIP"),
unzip it, then `cd` into the folder.

**Step 3 — make a virtual environment.** This keeps the project's packages
separate from the rest of your computer, which is what pants was doing for you
on the work laptop:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

If PowerShell refuses with a message about *execution policies*, it is blocking
scripts by default. Allow them for your user, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

**Step 4 — install the packages:**

```powershell
pip install streamlit pandas numpy matplotlib scikit-learn
```

This takes a couple of minutes the first time.

### Running it

With `(.venv)` showing in your prompt, from the top-level `work-experience`
folder:

```powershell
$env:PYTHONPATH = "."
streamlit run src\python\app_v2.py
```

Your browser should open at `http://localhost:8501`. If it does not, open that
address yourself.

Press `Ctrl+C` in the terminal to stop it.

### Every time after that

The virtual environment is already built, so there are only three steps:

```powershell
cd work-experience
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
streamlit run src\python\app_v2.py
```

`PYTHONPATH` tells Python to treat the current folder as the top of the
project, so that `from src.python...` imports work. It resets when you close
the window, which is why it is in the list every time.

### If something goes wrong

| What you see | What it means |
| ------------ | ------------- |
| `python: command not found` or the Store opens | "Add python.exe to PATH" was not ticked. Re-run the installer, choose "Modify", tick it. |
| `ModuleNotFoundError: No module named 'src'` | `PYTHONPATH` is not set, or you are in the wrong folder. Run it from the top-level `work-experience` folder. |
| `ModuleNotFoundError: No module named 'streamlit'` | The virtual environment is not active. Look for `(.venv)` in your prompt. |
| `running scripts is disabled on this system` | See the `Set-ExecutionPolicy` command in Step 3. |
| `streamlit: command not found` | Same as above — activate the virtual environment first. |

## Where the data comes from

`data_load()` in `src/python/main.py` returns **generated fake data**, made by
`src/python/load_data/fake_data.py`. Nothing is downloaded and no password is
needed, which is why this works on any machine.

The numbers are invented, but the *structure* is real: the same column names as
the plant database, plausible values and units for each sensor, a seasonal
drift across the year, and genuine relationships between the sensors and the
thing being predicted. So a model trained on it really does learn something —
you should see an R² around 0.9.

It uses a fixed random seed, so you get the same data every run. A score you
see today will be the same tomorrow, which makes it much easier to tell whether
a change you made actually improved anything.

The real plant data lives in ClickHouse. The code that loaded it is still there
as `load_from_clickhouse()` in `main.py`, for reference — it needs credentials
and database access that are no longer set up.

## Layout

```text
3rdparty/python/     Third-party dependency list (requirements.txt)
lockfiles/           Pinned dependency versions - generated, don't edit by hand
src/python/load_data/     Phase 1: loading plant data from ClickHouse
src/python/soft_sensors/  Phase 2: the SHC model
src/python/dashboards/    Phase 3: Streamlit dashboards
pants-plugins/macros/     Our own pants macros (e.g. streamlit_dashboard)
src/infra/           Terraform: cloud infrastructure
```

Every directory with Python code has a `BUILD` file. That is how Pants knows
what to test and lint. If you add a new directory, add a `BUILD` file
containing `python_sources()`, or run `pants tailor ::` to create it for you.

## Adding a dependency

Add it to `3rdparty/python/requirements.txt`, then regenerate the lockfile:

```bash
pants generate-lockfiles --resolve=python-default
```

## Connecting to ClickHouse

**You do not need this any more** — the project now uses generated data, as
described in [Where the data comes from](#where-the-data-comes-from). This is
kept as a note on how it worked.

The loader read its credentials from environment variables, so that no
passwords were ever committed to git:

```bash
export CLICKHOUSE_HOST=...
export CLICKHOUSE_USER=...
export CLICKHOUSE_PASSWORD=...
export CLICKHOUSE_DATABASE=...
```

That is a habit worth keeping for any project: secrets go in environment
variables or a git-ignored file, never in a file git tracks.
