"""Read-only access to completed recovery experiments."""

from functools import lru_cache
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES = PROJECT_ROOT / "results" / "tables"

CHANNEL_FILES = {
    "iid": TABLES / "unified_recovery_results.csv",
    "burst": TABLES / "burst_recovery_results.csv",
}


@lru_cache(maxsize=2)
def load_experiments(channel: str):
    if channel not in CHANNEL_FILES:
        raise ValueError("channel must be 'iid' or 'burst'")

    df = pd.read_csv(CHANNEL_FILES[channel])

    if channel == "iid":
        df = df.rename(
            columns={
                "loss_rate": "target_loss_rate",
                "exact_recovery_rate": "recovery_rate",
            }
        )
    else:
        df = df.rename(
            columns={
                "source_packet_recovery_rate": "recovery_rate",
            }
        )

    required = {
        "method",
        "target_loss_rate",
        "seed",
        "recovery_rate",
        "source_packets",
    }

    if not required.issubset(df.columns):
        raise ValueError("Experimental CSV is missing required columns")

    return df


def experimental_results(channel: str):
    df = load_experiments(channel)

    grouped = (
        df.groupby(
            ["method", "target_loss_rate"],
            as_index=False,
        )
        .agg(
            trials=("seed", "count"),
            mean_recovery=("recovery_rate", "mean"),
            std_recovery=("recovery_rate", "std"),
        )
        .sort_values(["method", "target_loss_rate"])
    )

    # Bootstrap confidence intervals are available for burst experiments only.
    confidence_lookup = {}

    if channel == "burst":
        confidence_path = TABLES / "recovery_confidence_intervals.csv"
        confidence_df = pd.read_csv(confidence_path)

        for ci in confidence_df.itertuples(index=False):
            key = (ci.method, round(float(ci.target_loss_rate), 8))
            confidence_lookup[key] = {
                "ci_lower": round(float(ci.ci_lower), 4),
                "ci_upper": round(float(ci.ci_upper), 4),
            }

    records = []

    for row in grouped.itertuples(index=False):
        records.append({
            "method": row.method,
            "loss_rate": float(row.target_loss_rate),
            "trials": int(row.trials),
            "mean_recovery_percent": round(
                float(row.mean_recovery) * 100, 4
            ),
            "std_recovery_pp": round(
                float(row.std_recovery) * 100, 4
            ),
            "confidence_interval": confidence_lookup.get(
                (row.method, round(float(row.target_loss_rate), 8))
            ),
        })

    return {
        "channel": channel,
        "total_trials": len(df),
        "methods": sorted(df["method"].unique().tolist()),
        "loss_rates": sorted(
            float(rate)
            for rate in df["target_loss_rate"].unique()
        ),
        "results": records,
    }
