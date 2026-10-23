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

df = df[
    df["target_loss_rate"] == 0.25
].copy()

fig, ax = plt.subplots(figsize=(11, 7))

for method, row in df.set_index("method").iterrows():

    ax.scatter(
        row["redundancy_percent"],
        row["recovery_percent"],
        s=110,
        label=method,
    )

ax.set_xlabel(
    "Transmission Redundancy (%)",
    fontsize=12,
)

ax.set_ylabel(
    "Source Packet Recovery (%)",
    fontsize=12,
)

ax.set_title(
    "Recovery vs. Redundancy at 25% Burst Loss",
    fontsize=14,
    fontweight="bold",
)

ax.set_xlim(-5, 110)
ax.set_ylim(0, 105)

ax.grid(True, linestyle="--", alpha=0.35)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.15),
    ncol=2,
    fontsize=9,
)

fig.tight_layout()

png_path = OUTPUT / "redundancy_recovery_tradeoff.png"
pdf_path = OUTPUT / "redundancy_recovery_tradeoff.pdf"

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
print("PASS: Redundancy-recovery graph generated.")