from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import t
from math import sqrt

tables = Path("results/tables")
tables.mkdir(parents=True, exist_ok=True)

random_df = pd.read_csv(tables / "unified_recovery_results.csv")
burst_df = pd.read_csv(tables / "burst_recovery_results.csv")
tests_df = pd.read_csv(tables / "burst_pairwise_comparisons_final.csv")

# 1. Random-loss summary: one row per method and configured loss rate.
random_summary = (
    random_df.groupby(["method", "loss_rate"], as_index=False)
    .agg(
        trials=("seed", "nunique"),
        mean_recovery=("exact_recovery_rate", "mean"),
        std_recovery=("exact_recovery_rate", "std"),
        full_recovery_fraction=("full_source_recovery", "mean"),
        mean_packets_sent=("transmitted_packets", "mean"),
        mean_encoding_seconds=("encoding_seconds", "mean"),
        mean_decoding_seconds=("decoding_seconds", "mean"),
    )
)

random_summary["mean_recovery_pct"] = random_summary["mean_recovery"] * 100
random_summary["std_recovery_pp"] = random_summary["std_recovery"] * 100
random_summary["full_recovery_pct"] = (
    random_summary["full_recovery_fraction"] * 100
)
random_summary["configured_loss_pct"] = random_summary["loss_rate"] * 100

random_summary.to_csv(tables / "random_loss_summary.csv", index=False)

# 2. Burst-loss summary and 95% t confidence intervals.
rows = []

for method, group in burst_df.groupby("method"):
    x = group["source_packet_recovery_rate"].dropna()
    n = len(x)
    mean = x.mean()
    sd = x.std(ddof=1)
    margin = t.ppf(0.975, n - 1) * sd / sqrt(n)

    rows.append({
        "method": method,
        "trials": n,
        "mean_recovery_pct": mean * 100,
        "std_recovery_pp": sd * 100,
        "ci_lower_pct": max(0, (mean - margin) * 100),
        "ci_upper_pct": min(100, (mean + margin) * 100),
        "full_recovery_pct": group["full_source_recovery"].mean() * 100,
        "mean_packets_sent": group["transmitted_packets"].mean(),
        "mean_encoding_seconds": group["encoding_seconds"].mean(),
        "mean_channel_seconds": group["channel_seconds"].mean(),
        "mean_decoding_seconds": group["decoding_seconds"].mean(),
    })

burst_summary = pd.DataFrame(rows)
burst_summary.to_csv(tables / "burst_loss_summary.csv", index=False)

# 3. Unified table. Channel models remain explicitly separate.
random_out = random_summary[[
    "method", "trials", "configured_loss_pct", "mean_recovery_pct",
    "std_recovery_pp", "full_recovery_pct", "mean_packets_sent",
    "mean_encoding_seconds", "mean_decoding_seconds"
]].copy()
random_out.insert(0, "channel_model", "Independent random packet loss")

burst_out = burst_summary[[
    "method", "trials", "mean_recovery_pct", "std_recovery_pp",
    "full_recovery_pct", "mean_packets_sent", "mean_encoding_seconds",
    "mean_decoding_seconds"
]].copy()
burst_out.insert(0, "channel_model", "Gilbert-Elliott burst packet loss")
burst_out["configured_loss_pct"] = np.nan

columns = [
    "channel_model", "method", "trials", "configured_loss_pct",
    "mean_recovery_pct", "std_recovery_pp", "full_recovery_pct",
    "mean_packets_sent", "mean_encoding_seconds", "mean_decoding_seconds"
]

combined = pd.concat(
    [random_out[columns], burst_out[columns]],
    ignore_index=True
)
combined.to_csv(tables / "consolidated_recovery_results.csv", index=False)

# 4. Regenerate a burst summary table for compatibility with existing scripts.
burst_summary.to_csv(tables / "burst_results_summary.csv", index=False)

# 5. Save the pairwise tests in a clean report-ready table.
tests_df.to_csv(tables / "final_statistical_comparisons.csv", index=False)

print("\n=== RANDOM-LOSS RESULTS ===")
print(random_summary[[
    "method", "configured_loss_pct", "mean_recovery_pct",
    "full_recovery_pct", "mean_packets_sent"
]].round(3).to_string(index=False))

print("\n=== BURST-LOSS RESULTS ===")
print(burst_summary[[
    "method", "mean_recovery_pct", "ci_lower_pct", "ci_upper_pct",
    "full_recovery_pct", "mean_packets_sent"
]].round(3).to_string(index=False))

print("\n=== STATISTICAL COMPARISONS ===")
print(tests_df[[
    "method_a", "method_b", "test",
    "mean_difference_percentage_points",
    "holm_adjusted_p_value", "significant_after_holm_0_05"
]].to_string(index=False))

print("\nCreated files:")
for name in [
    "random_loss_summary.csv",
    "burst_loss_summary.csv",
    "burst_results_summary.csv",
    "consolidated_recovery_results.csv",
    "final_statistical_comparisons.csv",
]:
    print(f"results/tables/{name}")
