# etl-quality-pipeline

A small, tested ETL pipeline: read a messy orders CSV with pandas, apply explicit data-quality rules, load clean rows into SQLite, and run a SQL revenue query. The run reports how many rows each rule fixed or dropped.

## Rules
Trim and lowercase `status`, drop exact duplicates, drop invalid dates, drop missing `customer_id`, drop non-positive `amount`, drop unknown `status`.

## Run
```bash
pip install -r requirements.txt
python -m pytest -q        # 4 tests
python -m etl.pipeline     # generates data/raw_orders.csv, writes data/orders.db, prints the quality report
```

## Data
The raw CSV is **synthetic** (`etl/generate.py`, fixed seed). Five defects are planted on purpose (duplicate, bad date, missing customer, negative amount, dirty status text), so the tests check that each is caught.

## Limits
Single-file batch job, no scheduler or incremental load. Dropping rows is a policy choice; a real pipeline would quarantine them in a rejects table.

## Provenance
A learning and portfolio project.
