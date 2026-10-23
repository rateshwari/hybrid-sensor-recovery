
from pathlib import Path
from math import sqrt

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import t

INPUT = Path("results/tables/burst_recovery_results.csv")
OUTPUT_DIR = Path("results/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

order = [
    "No ECC",
    "Reed-Solomon (8+2)",
    "Fountain (1.5x)",
    "Fountain (2.0x)",
]

summary = (
    df.groupby("method")
    .agg(
        mean_recovery=("source_packet_recovery_rate", "mean"),
        std_recovery=("source_packet_recovery_rate", "std"),
        trials=("source_packet_recovery_rate", "count"),
        full_recovery=("full_source_recovery", "mean"),
    )
    .reindex(order)
)

summary["margin"] = [
    t.ppf(0.975, n - 1) * sd / sqrt(n)
    for n, sd in zip(summary["trials"], summary["std_recovery"])
]

# Plot 1: Mean packet recovery with 95% confidence intervals.
fig, ax = plt.subplots(figsize=(9, 5.5))
x = range(len(summary))

ax.bar(
    list(x),
    summary["mean_recovery"] * 100,
    yerr=summary["margin"] * 100,
    capsize=5,
)
ax.set_xticks(list(x))
ax.set_xticklabels(summary.index, rotation=15, ha="right")
ax.set_ylabel("Exact source-packet recovery (%)")
ax.set_ylim(0, 105)
ax.set_title("Burst-Loss Recovery with 95% Confidence Intervals")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "burst_recovery_ci.png", dpi=300)
plt.close(fig)

# Plot 2: Fraction of trials recovering the entire source.
fig, ax = plt.subplots(figsize=(9, 5.5))
ax.bar(
    list(x),
    summary["full_recovery"] * 100,
)
ax.set_xticks(list(x))
ax.set_xticklabels(summary.index, rotation=15, ha="right")
ax.set_ylabel("Trials with full-source recovery (%)")
ax.set_ylim(0, 105)
ax.set_title("Full-Source Recovery under Burst Loss")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "burst_full_recovery.png", dpi=300)
plt.close(fig)

summary.to_csv(OUTPUT_DIR / "burst_results_summary.csv")

print(summary.to_string())
print(f"\nFigures and summary saved in: {OUTPUT_DIR}")
