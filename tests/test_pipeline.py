import pandas as pd

from etl.generate import generate
from etl.pipeline import clean, monthly_revenue, load, run


def test_generated_defects_are_caught(tmp_path):
    csv = tmp_path / "o.csv"
    generate(csv)
    df, issues = clean(pd.read_csv(csv))
    assert issues["input_rows"] == 201
    assert issues["duplicates_dropped"] == 1
    assert issues["invalid_date_dropped"] == 1
    assert issues["missing_customer_dropped"] == 1
    assert issues["non_positive_amount_dropped"] == 1
    assert issues["status_whitespace_or_case_fixed"] == 1
    assert issues["output_rows"] == 201 - 4
    assert (df["amount"] > 0).all()
    assert set(df["status"]) <= {"paid", "refunded", "pending"}


def test_clean_is_idempotent():
    raw = pd.DataFrame({"order_id": [1, 2], "customer_id": [1, 2], "order_date": ["2026-01-02", "2026-01-03"],
                        "amount": [10.0, 20.0], "status": ["paid", "pending"]})
    once, _ = clean(raw)
    twice, issues = clean(once.assign(order_date=once["order_date"].dt.strftime("%Y-%m-%d")))
    assert once.equals(twice) and issues["output_rows"] == 2


def test_monthly_revenue_only_counts_paid(tmp_path):
    df = pd.DataFrame({"order_id": [1, 2, 3], "customer_id": [1, 1, 2],
                       "order_date": pd.to_datetime(["2026-01-05", "2026-01-06", "2026-02-01"]),
                       "amount": [10.0, 99.0, 5.5], "status": ["paid", "refunded", "paid"]})
    db = str(tmp_path / "t.db")
    load(df, db)
    out = monthly_revenue(db)
    assert out.to_dict("records") == [
        {"month": "2026-01", "revenue": 10.0, "orders": 1},
        {"month": "2026-02", "revenue": 5.5, "orders": 1},
    ]


def test_run_end_to_end(tmp_path):
    csv = tmp_path / "o.csv"
    generate(csv)
    issues, rev = run(str(csv), str(tmp_path / "o.db"))
    assert issues["output_rows"] == 197 and len(rev) > 0
