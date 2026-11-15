# Data Warehouse - From API Data to Trusted Analytics

> PowerPoint presentation: https://constructoruniversity-my.sharepoint.com/:p:/g/personal/spremebida_constructor_university/cQp6V3FpfMw9Tb0xpJKK7dR_EgUBscTjGT4o_gNYhYDUWNYj3w

## How to setup everything?
1. Make a Git clone (check `how_to/git_commands.md`)
2. Setup the virtual enviroment (check `how_to/uv_enviroment.md`)
3. Collect the data 
   - ```bash uv run collect_data.py ```
4. Have fun


## What you find in this repo?

- `collect_data.py` is the ingestion script for the bronze layer of a medallion (bronze/silver/gold) data warehouse lab. It downloads all Nobel laureates from the public Nobel Prize API (v2.1, no key required), walking through the paginated /laureates endpoint with offset and limit until the total reported in meta.count is reached. Each page is saved **untouched** as a raw JSON file in data/bronze (e.g. laureates_offset0000.json), so the folder serves as the **source of truth** for later transformations. The script retries up to three times with exponential backoff on network errors, HTTP 429 and 5xx responses, waits half a second between requests, and lets the user change the page size (--page-size) as well as the output directory and API base URL through the BRONZE_DIR and NOBEL_API environment variables.
- `how_to/git_commands.md` is full of git commands to make this repo work at your computer. Follow the steps and make sure you don't have doubts before follow to the next tutorial.
- `how_to/uv_enviroment.md` how you will setup the virtual enviroment at your project and runs as I run at the class.
- `how_to/duckdb.md` explains more about how we do our work using the DuckDB and how/why we create the different layers (Bronze, Silver, Gold).
- `notebooks/1_nobel_lab_explore.ipynb` is where we look at the raw JSON files before building anything. Using an in-memory DuckDB connection, we check what is inside each file, open the nested list of laureates with `unnest`, and find the problems the next layers will have to fix: people and organisations mixed together, incomplete birth dates and laureates with more than one prize.
- `notebooks/2_nobel_lab_medallion.ipynb` builds the data warehouse step by step. It loads the pages **untouched** into bronze, cleans and types them into the silver tables (`laureates` and `awards`), and shapes them into the gold tables (`dim_laureate` and `fct_award`). Everything is saved in `data/nobel.duckdb`, and at the end we answer three questions: which countries have the most laureates, how old laureates are when they win, and how the share of women has changed.
- `notebooks/3_nobel_database.ipynb` shows what is inside the database file after it is built. It opens `data/nobel.duckdb` in read-only mode and lists the layers, the tables in each one, their columns and a few rows, so you know how to find and query any table later.
- `notebooks/4_nobel_lab_views.ipynb` is the data analysis part. It reads only from the gold tables and draws charts with matplotlib to understand the data visually: people and organisations, men and women, awards by category and by decade, shared prizes, age at award and countries of birth.

Run the notebooks in order: notebooks 3 and 4 need the database created by notebook 2.
