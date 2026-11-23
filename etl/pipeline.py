import sqlite3

import pandas as pd

VALID_STATUS = {"paid", "refunded", "pending"}


def clean(raw: pd.DataFrame):
    """Apply quality rules. Returns (clean_df, issues) with row counts per rule."""
    df = raw.copy()
    issues = {"input_rows": len(df)}

    raw_status = df["status"].astype(str)
    df["status"] = raw_status.str.strip().str.lower()
    issues["status_whitespace_or_case_fixed"] = int((raw_status != df["status"]).sum())

    before = len(df)
    df = df.drop_duplicates()
    issues["duplicates_dropped"] = before - len(df)

    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
    bad = df["order_date"].isna()
    issues["invalid_date_dropped"] = int(bad.sum())
    df = df[~bad]

    missing = df["customer_id"].isna()
    issues["missing_customer_dropped"] = int(missing.sum())
    df = df[~missing]

    neg = df["amount"] <= 0
    issues["non_positive_amount_dropped"] = int(neg.sum())
    df = df[~neg]

    unk = ~df["status"].isin(VALID_STATUS)
    issues["unknown_status_dropped"] = int(unk.sum())
    df = df[~unk]

    df = df.astype({"customer_id": "int64"})
    issues["output_rows"] = len(df)
    return df.reset_index(drop=True), issues


def load(df: pd.DataFrame, db_path: str) -> None:
    with sqlite3.connect(db_path) as con:
        df.assign(order_date=df["order_date"].dt.strftime("%Y-%m-%d")).to_sql(
            "orders", con, if_exists="replace", index=False
        )


def monthly_revenue(db_path: str) -> pd.DataFrame:
    q = """SELECT substr(order_date,1,7) AS month, ROUND(SUM(amount),2) AS revenue, COUNT(*) AS orders
           FROM orders WHERE status = 'paid' GROUP BY month ORDER BY month"""
    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query(q, con)


def run(csv_path: str, db_path: str):
    df, issues = clean(pd.read_csv(csv_path))
    load(df, db_path)
    return issues, monthly_revenue(db_path)


if __name__ == "__main__":
    from pathlib import Path

    from etl.generate import generate

    Path("data").mkdir(exist_ok=True)
    generate(Path("data/raw_orders.csv"))
    issues, rev = run("data/raw_orders.csv", "data/orders.db")
    for k, v in issues.items():
        print(f"{k}: {v}")
    print(rev.to_string(index=False))
