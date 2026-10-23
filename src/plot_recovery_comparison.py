from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

DATA = Path(
    "results/tables/final_performance_comparison.csv"
)

OUTPUT = Path("results/figures")
OUTPUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA)

fig, ax = plt.subplots(figsize=(12, 7))

for method, group in df.groupby("method"):
    group = group.sort_values("target_loss_rate")

    ax.plot(
        group["target_loss_rate"] * 100,
        group["recovery_percent"],
        marker="o",
        linewidth=2,
        markersize=5,
        label=method,
    )

ax.set_xlabel("Target Burst Packet Loss (%)", fontsize=12)
ax.set_ylabel("Source Packet Recovery (%)", fontsize=12)

ax.set_title(
    "Packet Recovery Performance Under Burst Loss",
    fontsize=14,
    fontweight="bold",
)

ax.set_xticks([5, 10, 25, 50, 75])
ax.set_ylim(0, 105)

ax.grid(True, linestyle="--", alpha=0.35)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=2,
    fontsize=9,
)

fig.tight_layout()

png_path = OUTPUT / "burst_recovery_comparison.png"
pdf_path = OUTPUT / "burst_recovery_comparison.pdf"

fig.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight",
)

fig.savefig(
    pdf_path,
    bbox_inches="tight",
)

plt.close(fig)

print("Saved:", png_path)
print("Saved:", pdf_path)
print("PASS: Recovery comparison graph generated.")
