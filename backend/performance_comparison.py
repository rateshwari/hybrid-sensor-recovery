"""Read-only access to aggregated burst-channel performance results."""

from functools import lru_cache
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "tables"
    / "final_performance_comparison.csv"
)

METRICS = {
    "recovery_percent": "%",
    "redundancy_percent": "%",
    "encoding_ms": "ms",
    "decoding_ms": "ms",
    "encoding_memory_kib": "KiB",
    "decoding_memory_kib": "KiB",
}


@lru_cache(maxsize=1)
def performance_comparison_results():
    df = pd.read_csv(RESULTS_PATH)

    required = {
        "method",
        "target_loss_rate",
        "trials",
        *METRICS.keys(),
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Performance results missing columns: {sorted(missing)}"
        )

    if df[list(required)].isna().any().any():
        raise ValueError("Performance results contain missing values.")

    if df.duplicated(["method", "target_loss_rate"]).any():
        raise ValueError("Duplicate method/loss-rate configurations.")

    records = []

    for row in df.sort_values(
        ["target_loss_rate", "method"]
    ).itertuples(index=False):
        record = {
            "method": str(row.method),
            "target_loss_rate": float(row.target_loss_rate),
            "trials": int(row.trials),
        }

        for metric in METRICS:
            record[metric] = round(float(getattr(row, metric)), 4)

        records.append(record)

    return {
        "channel": "burst",
        "source": "final_performance_comparison.csv",
        "metrics": METRICS,
        "methods": sorted(df["method"].unique().tolist()),
        "loss_rates": sorted(
            df["target_loss_rate"].astype(float).unique().tolist()
        ),
        "results": records,
    }
