"""Create a deterministic raw orders CSV with deliberate data defects."""
import csv
import random
from pathlib import Path


def generate(path: Path, n: int = 200, seed: int = 7) -> None:
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "order_id": i,
            "customer_id": rng.randint(1, 30),
            "order_date": f"2026-0{rng.randint(1, 9)}-{rng.randint(1, 28):02d}",
            "amount": round(rng.uniform(5, 500), 2),
            "status": rng.choice(["paid", "refunded", "pending"]),
        })
    rows[3]["amount"] = -20          # negative amount
    rows[10]["order_date"] = "31/02/2026"  # bad date
    rows[17]["customer_id"] = ""     # missing customer
    rows[25]["status"] = "PAID "     # dirty category
    rows.append(dict(rows[40]))      # exact duplicate
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
