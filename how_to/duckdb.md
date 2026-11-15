# DuckDB

[DuckDB](https://duckdb.org/) is an analytical database that runs inside your Python process. There is no server to install, no user and no password: the whole database is a single file on your disk. In this lab it is the engine that builds the three layers of the medallion architecture (bronze, silver, gold) from the JSON files collected by `collect_data.py`.

## Documentation

- [Documentation home](https://duckdb.org/docs/stable/)
- [Python API](https://duckdb.org/docs/stable/clients/python/overview)
- [Reading JSON files](https://duckdb.org/docs/stable/data/json/overview)
- [SQL reference](https://duckdb.org/docs/stable/sql/introduction)
- [`unnest` (lists and structs)](https://duckdb.org/docs/stable/sql/query_syntax/unnest)

## Install

With the `nobel` environment active (see [uv_enviroment.md](uv_enviroment.md)):

```bash
uv add duckdb
```

## Why we need a connection

A connection is the link between your Python code and one database. Every query goes through it, and it decides three things:

- **Where the data lives.** `duckdb.connect("data/nobel.duckdb")` opens that file, creating it if it does not exist. Every table you create is saved there and is still there the next time you connect.
- **Whether the data survives.** `duckdb.connect()` with no file name opens an in-memory database: it works the same way, but everything disappears when the program ends. Without a connection to a file, the bronze, silver and gold tables would have to be rebuilt on every run.
- **That every step sees the same tables.** The silver layer reads the bronze tables, and the gold layer reads the silver tables. This only works if all three steps use the same connection (or connect to the same file).

```python
import duckdb

con = duckdb.connect("data/nobel.duckdb")   # open (or create) the database file

con.sql("SELECT 42 AS answer").show()       # run a query through the connection

con.close()                                 # save and release the file
```

Only one process can write to a database file at a time. If you get a "file is locked" error, another notebook or script still has the file open: close that connection first. To only read, use `duckdb.connect("data/nobel.duckdb", read_only=True)`.

## Essential commands

Python side:

| Command | What it does |
| --- | --- |
| `con = duckdb.connect("data/nobel.duckdb")` | Open the database file |
| `con.sql("...")` | Run a SQL statement |
| `con.sql("...").show()` | Run a query and print the result |
| `con.sql("...").df()` | Return the result as a pandas DataFrame (needs `pandas`) |
| `con.sql("...").fetchall()` | Return the result as a list of Python tuples |
| `con.close()` | Close the connection |

SQL side:

| Command | What it does |
| --- | --- |
| `CREATE SCHEMA IF NOT EXISTS silver` | Create a schema (a folder for tables) |
| `CREATE OR REPLACE TABLE s.t AS SELECT ...` | Create a table from a query, replacing the old one |
| `SHOW ALL TABLES` | List every table in every schema |
| `DESCRIBE s.t` | Show the columns and types of a table |
| `SUMMARIZE s.t` | Show statistics (min, max, nulls, ...) for each column |
| `SELECT * FROM s.t LIMIT 5` | Look at the first rows |
| `SELECT * FROM read_json_auto('folder/*.json')` | Query JSON files directly, as if they were a table |
| `unnest(list_column)` | Turn a list into one row per element |
| `TRY_CAST(x AS DATE)` | Convert a type, returning `NULL` instead of failing |
| `COPY s.t TO 'file.csv'` (or `.parquet`) | Export a table to a file |

## How DuckDB builds the medallion layers

Each layer is a schema inside the same database file, and each step is a `CREATE OR REPLACE TABLE ... AS SELECT` that reads from the layer before it:

```
data/bronze/*.json  ->  bronze.laureates_raw  ->  silver.laureates  ->  gold.prizes_by_category_decade
   (files on disk)        (raw, as received)      silver.prizes           (ready for analysis)
                                                  (clean, typed)
```

Start by connecting and creating the three schemas:

```python
import duckdb

con = duckdb.connect("data/nobel.duckdb")

con.sql("CREATE SCHEMA IF NOT EXISTS bronze")
con.sql("CREATE SCHEMA IF NOT EXISTS silver")
con.sql("CREATE SCHEMA IF NOT EXISTS gold")
```

### Bronze: load the data as it arrived

DuckDB reads all the JSON files at once and works out the columns by itself. Nothing is cleaned or changed. We only add where each row came from and when it was loaded, so every later result can be traced back to its source file.

```python
con.sql("""
    CREATE OR REPLACE TABLE bronze.laureates_raw AS
    SELECT *, now() AS loaded_at
    FROM read_json_auto('data/bronze/laureates_offset*.json', filename = true)
""")
```

The table has one row per file (one API page). The `laureates` column holds the list of 100 laureates of that page, still nested exactly as the API returned it.

### Silver: clean, typed, one row per thing

Here DuckDB does the actual transformation work:

- `unnest` opens the lists: one row per laureate, and one row per prize.
- Dot notation (`l.birth.place.country.en`) reaches into the nested JSON.
- `CAST` / `TRY_CAST` turn text into real numbers and dates. Some birth dates are incomplete (e.g. `1943-00-00`); `TRY_CAST` turns them into `NULL` instead of stopping the load.
- `coalesce` handles organizations, which have `orgName` instead of `knownName`.

```python
con.sql("""
    CREATE OR REPLACE TABLE silver.laureates AS
    SELECT DISTINCT
        CAST(l.id AS INTEGER)                  AS laureate_id,
        coalesce(l.knownName.en, l.orgName.en) AS name,
        l.gender                               AS gender,
        TRY_CAST(l.birth.date AS DATE)         AS birth_date,
        l.birth.place.country.en               AS birth_country
    FROM (SELECT unnest(laureates) AS l FROM bronze.laureates_raw)
""")

con.sql("""
    CREATE OR REPLACE TABLE silver.prizes AS
    SELECT DISTINCT
        CAST(l.id AS INTEGER)        AS laureate_id,
        CAST(p.awardYear AS INTEGER) AS award_year,
        p.category.en                AS category,
        p.prizeAmount                AS prize_amount
    FROM (
        SELECT l, unnest(l.nobelPrizes) AS p
        FROM (SELECT unnest(laureates) AS l FROM bronze.laureates_raw)
    )
""")
```

A laureate can win more than once, which is why prizes get their own table linked by `laureate_id`.

### Gold: answers to business questions

Gold tables are small, aggregated and ready for a chart or a report. They read only from silver, never from bronze.

```python
con.sql("""
    CREATE OR REPLACE TABLE gold.prizes_by_category_decade AS
    SELECT
        category,
        (award_year // 10) * 10                         AS decade,
        count(*)                                        AS prizes,
        count(*) FILTER (WHERE l.gender = 'female')     AS prizes_to_women
    FROM silver.prizes p
    JOIN silver.laureates l USING (laureate_id)
    GROUP BY ALL
    ORDER BY category, decade
""")
```

### Check the result

```python
con.sql("SHOW ALL TABLES").show()
con.sql("SELECT * FROM gold.prizes_by_category_decade LIMIT 5").show()

con.close()
```

Because every step is `CREATE OR REPLACE`, you can run the whole script again at any time: the layers are rebuilt from the bronze files and the result is the same.
