"""Repeated timing benchmark for burst-loss recovery."""

from pathlib import Path

import pandas as pd

from burst_experiment import run_trial


LOSS_RATES = [0.05, 0.10, 0.25, 0.50, 0.75]
TRIALS = 30

OUTPUT_PATH = Path(
    "results/tables/timing_results.csv"
)


def run_experiment():
    rows = []

    for loss_rate in LOSS_RATES:
        for trial in range(TRIALS):
            seed = 42 + trial

            print(
                f"Loss: {loss_rate:.0%} | "
                f"Trial: {trial + 1}/{TRIALS}",
                flush=True,
            )

            trial_rows = run_trial(
                seed=seed,
                loss_rate=loss_rate,
            )

            rows.extend(trial_rows)

    summary = pd.DataFrame(rows)

    expected_records = (
        len(LOSS_RATES) * TRIALS * 10
    )

    assert len(summary) == expected_records, (
        f"Expected {expected_records} records, "
        f"got {len(summary)}"
    )

    assert summary[
        ["encoding_seconds", "decoding_seconds"]
    ].notna().all().all()

    assert (
        summary[
            ["encoding_seconds", "decoding_seconds"]
        ] >= 0
    ).all().all()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(OUTPUT_PATH, index=False)

    print("\n=== TIMING EXPERIMENT COMPLETE ===")
    print(f"Total records: {len(summary)}")
    print(f"Configurations: {summary['method'].nunique()}")
    print(f"Loss levels: {summary['target_loss_rate'].nunique()}")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nPASS: Timing benchmark completed.")


if __name__ == "__main__":
    run_experiment()
