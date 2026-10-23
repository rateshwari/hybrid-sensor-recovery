from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("results/tables/unified_performance_results.csv")
OUTPUT = Path("results/tables/paired_interleaving_results.csv")

df = pd.read_csv(DATA)

rng = np.random.default_rng(42)
records = []

for parity in [2, 4, 8]:

    standard_name = f"Reed-Solomon (8+{parity})"
    interleaved_name = f"Reed-Solomon Interleaved (8+{parity})"

    standard = df[
        df["method"] == standard_name
    ][
        ["seed", "target_loss_rate", "source_packet_recovery_rate"]
    ].rename(columns={
        "source_packet_recovery_rate": "standard_recovery"
    })

    interleaved = df[
        df["method"] == interleaved_name
    ][
        ["seed", "target_loss_rate", "source_packet_recovery_rate"]
    ].rename(columns={
        "source_packet_recovery_rate": "interleaved_recovery"
    })

    paired = standard.merge(
        interleaved,
        on=["seed", "target_loss_rate"],
        validate="one_to_one",
    )

    assert len(paired) == 150

    for loss, group in paired.groupby("target_loss_rate"):

        differences = (
            group["interleaved_recovery"].to_numpy()
            - group["standard_recovery"].to_numpy()
        ) * 100

        assert len(differences) == 30

        bootstrap = rng.choice(
            differences,
            size=(10000, len(differences)),
            replace=True,
        ).mean(axis=1)

        lower, upper = np.percentile(
            bootstrap,
            [2.5, 97.5],
        )

        records.append({
            "parity": parity,
            "target_loss_rate": loss,
            "trials": len(differences),
            "mean_gain_pp": differences.mean(),
            "ci_lower_pp": lower,
            "ci_upper_pp": upper,
        })

results = pd.DataFrame(records)

assert len(results) == 15
assert (results["trials"] == 30).all()

results.to_csv(OUTPUT, index=False)

print("\n=== INTERLEAVING GAIN AT 25% BURST LOSS ===")

selected = results[
    np.isclose(results["target_loss_rate"], 0.25)
]

print(
    selected[
        [
            "parity",
            "mean_gain_pp",
            "ci_lower_pp",
            "ci_upper_pp",
        ]
    ].round(3).to_string(index=False)
)

print("\n=== INTERLEAVING GAIN ACROSS ALL LOSS LEVELS ===")

pivot = results.pivot(
    index="parity",
    columns="target_loss_rate",
    values="mean_gain_pp",
)

pivot.columns = [
    f"{loss:.0%} loss"
    for loss in pivot.columns
]

print(pivot.round(2).to_string())

print("\nSaved:", OUTPUT)
print("PASS: Paired interleaving analysis completed.")
