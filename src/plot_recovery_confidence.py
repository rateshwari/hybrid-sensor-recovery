from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA = Path("results/tables/unified_performance_results.csv")
FIGURES = Path("results/figures")
TABLES = Path("results/tables")

FIGURES.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)

required = [
    "method",
    "seed",
    "target_loss_rate",
    "source_packet_recovery_rate",
]

assert df[required].notna().all().all()
assert not df.duplicated(
    ["method", "seed", "target_loss_rate"]
).any()

rng = np.random.default_rng(42)

records = []

for (method, loss), group in df.groupby(
    ["method", "target_loss_rate"]
):
    values = (
        group["source_packet_recovery_rate"]
        .to_numpy(dtype=float) * 100
    )

    assert len(values) == 30

    bootstrap_samples = rng.choice(
        values,
        size=(10000, len(values)),
        replace=True,
    )

    bootstrap_means = bootstrap_samples.mean(axis=1)

    lower, upper = np.percentile(
        bootstrap_means,
        [2.5, 97.5],
    )

    records.append({
        "method": method,
        "target_loss_rate": loss,
        "trials": len(values),
        "mean_recovery_percent": values.mean(),
        "ci_lower": lower,
        "ci_upper": upper,
    })

summary = pd.DataFrame(records)

assert len(summary) == 50

csv_path = TABLES / "recovery_confidence_intervals.csv"

summary.to_csv(csv_path, index=False)

fig, ax = plt.subplots(figsize=(12, 8))

for method, group in summary.groupby("method"):
    group = group.sort_values("target_loss_rate")

    x = group["target_loss_rate"].to_numpy() * 100
    y = group["mean_recovery_percent"].to_numpy()

    lower_error = y - group["ci_lower"].to_numpy()
    upper_error = group["ci_upper"].to_numpy() - y

    ax.errorbar(
        x,
        y,
        yerr=[lower_error, upper_error],
        marker="o",
        capsize=3,
        linewidth=1.7,
        markersize=4,
        label=method,
    )

ax.set_xlabel("Target Burst Packet Loss (%)")
ax.set_ylabel("Mean Source Packet Recovery (%)")

ax.set_title(
    "Packet Recovery with 95% Bootstrap Confidence Intervals"
)

ax.set_xticks([5, 10, 25, 50, 75])
ax.set_ylim(0, 105)

ax.grid(True, linestyle="--", alpha=0.3)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=2,
    fontsize=9,
)

fig.tight_layout()

png_path = FIGURES / "recovery_confidence_intervals.png"
pdf_path = FIGURES / "recovery_confidence_intervals.pdf"

fig.savefig(png_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf_path, bbox_inches="tight")

plt.close(fig)

print("\n=== CONFIDENCE INTERVAL VALIDATION ===")
print("Configurations:", summary["method"].nunique())
print("Loss levels:", summary["target_loss_rate"].nunique())
print("Total conditions:", len(summary))
print("Trials per condition:", summary["trials"].min())

print("\n=== 25% BURST LOSS CONFIDENCE INTERVALS ===")

selected = summary[
    np.isclose(summary["target_loss_rate"], 0.25)
]

print(
    selected[
        [
            "method",
            "mean_recovery_percent",
            "ci_lower",
            "ci_upper",
        ]
    ].round(2).to_string(index=False)
)

print("\nSaved:", csv_path)
print("Saved:", png_path)
print("Saved:", pdf_path)
print("PASS: Bootstrap confidence interval analysis completed.")