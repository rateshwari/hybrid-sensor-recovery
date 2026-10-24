"""Read-only paired interleaving gain results."""

from functools import lru_cache
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "tables"
    / "paired_interleaving_results.csv"
)


@lru_cache(maxsize=1)
def interleaving_gain_results():
    df = pd.read_csv(RESULTS_PATH)

    required = {
        "parity",
        "target_loss_rate",
        "trials",
        "mean_gain_pp",
        "ci_lower_pp",
        "ci_upper_pp",
    }

    if not required.issubset(df.columns):
        raise ValueError("Paired results CSV has missing columns.")

    if df[list(required)].isna().any().any():
        raise ValueError("Paired results CSV contains missing values.")

    records = []

    for row in df.sort_values(
        ["parity", "target_loss_rate"]
    ).itertuples(index=False):
        records.append({
            "parity": int(row.parity),
            "target_loss_rate": float(row.target_loss_rate),
            "trials": int(row.trials),
            "mean_gain_pp": round(float(row.mean_gain_pp), 4),
            "ci_lower_pp": round(float(row.ci_lower_pp), 4),
            "ci_upper_pp": round(float(row.ci_upper_pp), 4),
        })

    return {
        "channel": "burst",
        "comparison": "RS Interleaved minus Standard RS",
        "unit": "percentage points",
        "confidence_level": 0.95,
        "parity_values": sorted(df["parity"].astype(int).unique().tolist()),
        "loss_rates": sorted(
            df["target_loss_rate"].astype(float).unique().tolist()
        ),
        "results": records,
    }
