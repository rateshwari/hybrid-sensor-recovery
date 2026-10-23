from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA = Path("results/tables/paired_interleaving_results.csv")
OUTPUT = Path("results/figures")
OUTPUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)

assert len(df) == 15
assert (df["trials"] == 30).all()

fig, ax = plt.subplots(figsize=(11, 7))

for parity, group in df.groupby("parity"):

    group = group.sort_values("target_loss_rate")

    x = group["target_loss_rate"].to_numpy() * 100
    y = group["mean_gain_pp"].to_numpy()

    lower = y - group["ci_lower_pp"].to_numpy()
    upper = group["ci_upper_pp"].to_numpy() - y

    ax.errorbar(
        x,
        y,
        yerr=[lower, upper],
        marker="o",
        linewidth=2,
        capsize=4,
        label=f"RS (8+{parity})",
    )

ax.axhline(
    0,
    linestyle="--",
    linewidth=1.2,
    color="black",
    label="No improvement",
)

ax.set_xlabel("Target Burst Packet Loss (%)", fontsize=12)
ax.set_ylabel(
    "Interleaving Recovery Gain (percentage points)",
    fontsize=12,
)

ax.set_title(
    "Effect of Interleaving on Reed-Solomon Recovery",
    fontsize=14,
    fontweight="bold",
)

ax.set_xticks([5, 10, 25, 50, 75])
ax.grid(True, linestyle="--", alpha=0.3)
ax.legend()

fig.tight_layout()

png_path = OUTPUT / "interleaving_gain.png"
pdf_path = OUTPUT / "interleaving_gain.pdf"

fig.savefig(png_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf_path, bbox_inches="tight")

plt.close(fig)

print("Saved:", png_path)
print("Saved:", pdf_path)
print("PASS: Interleaving gain graph generated.")
