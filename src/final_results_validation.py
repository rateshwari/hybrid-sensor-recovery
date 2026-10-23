from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("results/tables")

data = pd.read_csv(
    BASE / "unified_performance_results.csv"
)

summary = pd.read_csv(
    BASE / "final_performance_comparison.csv"
)

keys = ["method", "seed", "target_loss_rate"]

print("\n=== FINAL EXPERIMENT VALIDATION ===")

assert len(data) == 1500
assert data["method"].nunique() == 10
assert data["target_loss_rate"].nunique() == 5

assert not data.duplicated(keys).any()
assert not data.isna().any().any()

counts = data.groupby(
    ["method", "target_loss_rate"]
).size()

assert len(counts) == 50
assert (counts == 30).all()

assert data[
    "source_packet_recovery_rate"
].between(0, 1).all()

assert data[
    "redundancy_percent"
].ge(0).all()

assert (
    data["recovered_source_packets"]
    <= data["source_packets"]
).all()

assert (
    data["recovered_source_packets"] >= 0
).all()

assert np.allclose(
    data["source_packet_recovery_rate"],
    data["recovered_source_packets"]
    / data["source_packets"],
    atol=1e-8,
)

assert (
    data[
        [
            "encoding_peak_memory_kib",
            "decoding_peak_memory_kib",
            "encoding_ms",
            "decoding_ms",
        ]
    ] >= 0
).all().all()

recalculated = (
    data.groupby(
        ["method", "target_loss_rate"]
    )["source_packet_recovery_rate"]
    .mean()
    .mul(100)
    .reset_index(name="recalculated_recovery")
)

check = summary.merge(
    recalculated,
    on=["method", "target_loss_rate"],
    validate="one_to_one",
)

assert len(check) == 50

# Summary CSV stores recovery percentages to 3 decimal places.
# Maximum expected rounding difference is 0.0005 percentage points.

assert np.allclose(
    check["recovery_percent"],
    check["recalculated_recovery"],
    atol=0.0005,
    rtol=0,
)

print("Total records:", len(data))
print("Configurations:", data["method"].nunique())
print("Loss levels:", data["target_loss_rate"].nunique())
print("Trials per condition:", counts.min())
print("Summary records:", len(summary))

print("\nPASS: All final experimental data checks passed.")