# Python environment with uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and environment manager. We use it to create an isolated virtual environment for this project, so the libraries you install here do not affect the rest of your computer.

Run every command below from the project folder (`datawarehouse-nobel`). If you do not have the project yet, see [git_commands.md](git_commands.md).

## What you need

- A terminal (macOS/Linux) or PowerShell (Windows).
- An internet connection.
- uv itself. You do not need to install Python first: uv can download it for you.

## 1. Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen the terminal, then check that it worked:

```bash
uv --version
```

If you do not have Python on your machine, install it with uv:

```bash
uv python install 3.12
```

## 2. Create and activate the virtual environment

We name the environment `nobel`, so you can tell it apart from the environments of your other projects:

```bash
uv venv --prompt nobel
```

This creates a `.venv` folder whose name shown in the terminal is `nobel`. The folder itself stays `.venv` because that is where uv looks for the project environment (`uv sync` and `uv run` depend on it). Activate it:

```bash
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

Your prompt now starts with `(nobel)`. You need to activate the environment again every time you open a new terminal. To leave it, run `deactivate`.

## 3. Install the libraries from requirements.txt

```bash
uv pip install -r requirements.txt
```

This reads `requirements.txt` and installs every library listed there into `.venv`.

## 4. Add or remove libraries

Install a new library:

```bash
uv pip install pandas
```

Remove a library:

```bash
uv pip uninstall pandas
```

See what is installed:

```bash
uv pip list
```

If you add or remove a library that the project depends on, update `requirements.txt` so everyone else gets the same change: add or delete the corresponding line in the file.

## 5. Collect the data

```bash
python collect_data.py
```

The raw JSON files are saved in `data/bronze`.

## 6. Share the environment with uv's own files (without requirements.txt)

Instead of maintaining `requirements.txt` by hand, uv can manage the project for you. It then describes the environment in two files, and those are what you share:

- `pyproject.toml`: the libraries the project needs directly (e.g. `requests`) and the Python version it supports.
- `uv.lock`: the exact version of every library installed, including the dependencies of your dependencies. This is what guarantees that everyone gets an identical environment.

### If you are the one sharing

Create the `pyproject.toml` (only once per project):

```bash
uv init --bare
```

Add the libraries the project uses. If you already have a `requirements.txt`, import it in one go:

```bash
uv add requests                 # one library
uv add -r requirements.txt      # everything listed in requirements.txt
```

Each `uv add` updates `pyproject.toml`, updates `uv.lock` and installs the library into `.venv`. To remove a library:

```bash
uv remove requests
```

Do not edit `uv.lock` by hand: uv rewrites it for you. Then commit both files so others receive them:

```bash
git add pyproject.toml uv.lock
git commit -m "Add uv project files"
git push
```

Never share the `.venv` folder itself: it is specific to your computer and is rebuilt from these two files.

### If you are the one receiving

After `git clone` or `git pull`, create the environment with the `nobel` name (only the first time) and install exactly what is in `uv.lock`:

```bash
uv venv --prompt nobel
uv sync
```

`uv sync` reuses the `.venv` you just created. If you skip the first command, `uv sync` still creates `.venv` by itself, but without the `nobel` name.

Then run the script through uv, which uses the project environment without you having to activate it:

```bash
uv run collect_data.py
```

### Which commands to use

When the project has a `pyproject.toml`, use `uv add` / `uv remove` instead of `uv pip install` / `uv pip uninstall`. Libraries installed with `uv pip install` are not recorded in `pyproject.toml` or `uv.lock`, so nobody else receives them, and the next `uv sync` removes them.
