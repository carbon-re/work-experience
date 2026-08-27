# Work Experience Repo

Welcome to your project!

This week you will build a machine learning model that predicts a cement plant's
**specific heat consumption** (SHC), then show the predictions in a dashboard.

SHC is the energy used to make one unit of clinker. If a plant makes 1 ton
(1000 kg) of clinker using 1,000,000 kcal of energy, its SHC is 1000 kcal/kg.
Lower is better: less fuel burnt means less CO2.

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

## Layout

```text
3rdparty/python/     Third-party dependency list (requirements.txt)
lockfiles/           Pinned dependency versions - generated, don't edit by hand
src/python/load_data/     Phase 1: loading plant data from ClickHouse
src/python/soft_sensors/  Phase 2: the SHC model
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

The data loader reads credentials from environment variables, so that no
passwords are ever committed to git:

```bash
export CLICKHOUSE_HOST=...
export CLICKHOUSE_USER=...
export CLICKHOUSE_PASSWORD=...
export CLICKHOUSE_DATABASE=...
```

Never put these in a file that git tracks. `.env` is git-ignored if you prefer
to keep them in a file.
