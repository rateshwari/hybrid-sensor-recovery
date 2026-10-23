"""Repeated memory profiling under burst packet loss."""

from pathlib import Path
import pandas as pd

from memory_experiment import (
    load_source_packets,
    measure_no_ecc_memory,
    measure_rs_encoding,
    measure_rs_decoding,
    measure_interleaved_rs,
    measure_fountain_encoding,
    measure_fountain_decoding,
)


LOSS_RATES = [0.05, 0.10, 0.25, 0.50, 0.75]
TRIALS = 30

PARITY_OPTIONS = [2, 4, 8]
FOUNTAIN_OVERHEADS = [1.25, 1.50, 2.00]

OUTPUT_PATH = Path(
    "results/tables/repeated_memory_results.csv"
)


def run_experiment():
    source_packets = load_source_packets()

    results = []

    for loss_rate in LOSS_RATES:
        for trial in range(TRIALS):
            seed = 42 + trial

            print(
                f"Loss: {loss_rate:.0%} | "
                f"Trial: {trial + 1}/{TRIALS}",
                flush=True,
            )

            # No ECC
            baseline = measure_no_ecc_memory(
                source_packets,
                seed=seed,
                loss_rate=loss_rate,
            )
            results.append({
                **baseline,
                "target_loss_rate": loss_rate,
                "trial": trial + 1,
                "seed": seed,
            })

            # Standard Reed-Solomon
            for parity_count in PARITY_OPTIONS:
                encoding = measure_rs_encoding(
                    source_packets,
                    parity_count,
                )

                decoding = measure_rs_decoding(
                    source_packets,
                    parity_count,
                    seed=seed,
                    loss_rate=loss_rate,
                )

                results.append({
                    **encoding,
                    **decoding,
                    "target_loss_rate": loss_rate,
                    "trial": trial + 1,
                    "seed": seed,
                })

            # Interleaved Reed-Solomon
            for parity_count in PARITY_OPTIONS:
                result = measure_interleaved_rs(
                    source_packets,
                    parity_count,
                    seed=seed,
                    loss_rate=loss_rate,
                )

                results.append({
                    **result,
                    "target_loss_rate": loss_rate,
                    "trial": trial + 1,
                    "seed": seed,
                })

            # Fountain
            for overhead in FOUNTAIN_OVERHEADS:
                encoding = measure_fountain_encoding(
                    source_packets,
                    overhead,
                    seed=seed,
                )

                decoding = measure_fountain_decoding(
                    source_packets,
                    overhead,
                    seed=seed,
                    loss_rate=loss_rate,
                )

                results.append({
                    **encoding,
                    **decoding,
                    "target_loss_rate": loss_rate,
                    "trial": trial + 1,
                    "seed": seed,
                })

    summary = pd.DataFrame(results)

    configurations = (
        1
        + 2 * len(PARITY_OPTIONS)
        + len(FOUNTAIN_OVERHEADS)
    )

    expected_records = (
        configurations * len(LOSS_RATES) * TRIALS
    )

    assert len(summary) == expected_records, (
        f"Expected {expected_records} records, "
        f"got {len(summary)}"
    )

    assert summary["encoding_peak_memory_kib"].notna().all()
    assert summary["decoding_peak_memory_kib"].notna().all()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(OUTPUT_PATH, index=False)

    print("\n=== MEMORY EXPERIMENT COMPLETE ===")
    print(f"Total records: {len(summary)}")
    print(f"Configurations: {summary['method'].nunique()}")
    print(f"Loss rates: {summary['target_loss_rate'].nunique()}")
    print(f"Saved to: {OUTPUT_PATH}")

    print("\nPASS: Repeated memory experiment completed.")


if __name__ == "__main__":
    run_experiment()
