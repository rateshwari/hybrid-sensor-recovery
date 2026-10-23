"""Evaluate Fountain decoding over repeated random-loss trials."""

from pathlib import Path
import random

import pandas as pd

from fountain import encode, decode


RESULT_PATH = Path("results/tables/fountain_validation.csv")

SOURCE_COUNT = 64
PACKET_SIZE = 64
OVERHEADS = [1.25, 1.5, 2.0]
LOSS_RATES = [0.05, 0.10, 0.20, 0.30]
TRIALS = 30


def make_source(seed: int):
    rng = random.Random(seed)
    return [
        bytes(rng.randrange(256) for _ in range(PACKET_SIZE))
        for _ in range(SOURCE_COUNT)
    ]


def run_trial(overhead: float, loss_rate: float, seed: int):
    source = make_source(seed)
    output_count = int(SOURCE_COUNT * overhead)

    encoded = encode(
        source,
        output_count=output_count,
        seed=seed,
    )

    rng = random.Random(seed + 1_000_003)
    received = [
        symbol for symbol in encoded
        if rng.random() >= loss_rate
    ]

    recovered = decode(received, source_count=SOURCE_COUNT)

    exact_count = sum(
        recovered[i] == source[i]
        for i in range(SOURCE_COUNT)
    )

    return {
        "seed": seed,
        "source_count": SOURCE_COUNT,
        "encoded_symbol_count": output_count,
        "received_symbol_count": len(received),
        "overhead_ratio": overhead,
        "loss_rate": loss_rate,
        "exact_recovery_rate": exact_count / SOURCE_COUNT,
        "full_source_recovery": exact_count == SOURCE_COUNT,
    }


def main():
    rows = []

    for overhead in OVERHEADS:
        for loss_rate in LOSS_RATES:
            for trial in range(TRIALS):
                rows.append(
                    run_trial(
                        overhead=overhead,
                        loss_rate=loss_rate,
                        seed=1000 + trial,
                    )
                )

    results = pd.DataFrame(rows)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULT_PATH, index=False)

    summary = (
        results.groupby(["overhead_ratio", "loss_rate"])
        .agg(
            mean_exact_recovery=("exact_recovery_rate", "mean"),
            full_recovery_fraction=("full_source_recovery", "mean"),
            mean_received_symbols=("received_symbol_count", "mean"),
        )
        .reset_index()
    )

    print("=== FOUNTAIN VALIDATION SUMMARY ===")
    print(summary.to_string(index=False))
    print(f"\nDetailed trials saved to: {RESULT_PATH}")


if __name__ == "__main__":
    main()
