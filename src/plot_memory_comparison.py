from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
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

df = df.sort_values("decoding_memory_kib")

methods = df["method"].tolist()
encoding = df["encoding_memory_kib"].to_numpy()
decoding = df["decoding_memory_kib"].to_numpy()

y = np.arange(len(methods))
bar_height = 0.36

fig, ax = plt.subplots(figsize=(12, 8))

ax.barh(
    y - bar_height / 2,
    encoding,
    height=bar_height,
    label="Encoding memory",
)

ax.barh(
    y + bar_height / 2,
    decoding,
    height=bar_height,
    label="Decoding memory",
)

ax.set_yticks(y)
ax.set_yticklabels(methods, fontsize=9)

ax.set_xlabel(
    "Peak Python-tracked Memory (KiB)",
    fontsize=12,
)

ax.set_title(
    "Encoding and Decoding Memory at 25% Burst Loss",
    fontsize=14,
    fontweight="bold",
)

ax.legend()
ax.grid(axis="x", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

fig.tight_layout()

png_path = OUTPUT / "memory_comparison.png"
pdf_path = OUTPUT / "memory_comparison.pdf"

fig.savefig(png_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf_path, bbox_inches="tight")

plt.close(fig)

print("Saved:", png_path)
print("Saved:", pdf_path)
print("PASS: Memory comparison graph generated.")
