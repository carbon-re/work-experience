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

## Getting started

This repo uses [Pants](https://www.pantsbuild.org/) as its build system. You
don't need to install Python packages yourself — Pants handles that.

Install Pants once:

```bash
curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
```

Then, from the repo root:

```bash
pants test ::          # run all the tests
pants lint ::          # check code style
pants fmt ::           # auto-format your code
pants green            # all of the above, before you commit
```

The first run downloads Python and the dependencies, so it takes a few
minutes. After that it is fast.

## Layout

```text
3rdparty/python/     Third-party dependency list (requirements.txt)
lockfiles/           Pinned dependency versions - generated, don't edit by hand
src/python/data/     Phase 1: loading plant data from ClickHouse
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
