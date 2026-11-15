# Git commands

How to download this repository, keep it up to date and send your own changes.

## What you need

[Git](https://git-scm.com/downloads) installed. Check with:

```bash
git --version
```

## 1. Clone the repository

Open a terminal in the folder where you want the project to live and run:

```bash
git clone https://github.com/sthemonica/datawarehouse-nobel.git
```

This creates a `datawarehouse-nobel` folder containing the project and its full history.

## 2. Enter the project folder

```bash
cd datawarehouse-nobel
```

## 3. Check that it worked

```bash
git status
```

You should see `On branch main` and `nothing to commit, working tree clean`.

## 4. Download the latest changes

Whenever the repository is updated, run this inside the project folder:

```bash
git pull
```

## 5. Send your own changes

See which files you changed:

```bash
git status
```

Choose the files that go into the next commit:

```bash
git add collect_data.py        # one file
git add .                      # everything that changed
```

Save them in the history with a short message describing what you did:

```bash
git commit -m "Describe your change here"
```

Send the commit to GitHub:

```bash
git push
```

`git push` only works if you have write access to the repository. If you do not, fork it on GitHub first and clone your fork instead.

## Next step

Set up the Python environment: see [uv_enviroment.md](uv_enviroment.md).
