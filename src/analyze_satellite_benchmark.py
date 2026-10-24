"""Statistical analysis of repeated satellite recovery experiments."""

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

INPUT = Path("results/satellite/benchmark_results.csv")
SUMMARY = Path("results/satellite/benchmark_summary.csv")
PAIRED = Path("results/satellite/interleaving_analysis.csv")

# Two-sided 95% Student-t critical value, df=29.
T_CRITICAL = 2.04523


def summarize(values):
    n = len(values)
    avg = mean(values)
    sd = stdev(values)
    margin = T_CRITICAL * sd / math.sqrt(n)

    return {
        "n": n,
        "mean": avg,
        "std": sd,
        "ci_lower": avg - margin,
        "ci_upper": avg + margin,
    }


def save_csv(path, rows):
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    with INPUT.open(newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 3000

    grouped = defaultdict(list)
    indexed = {}

    for row in rows:
        channel = row["channel"]
        loss = float(row["target_loss_rate"])
        seed = int(row["seed"])
        method = row["method"]

        key = (channel, loss, method)
        grouped[key].append(float(row["recovery"]))

        trial_key = (channel, loss, seed, method)
        assert trial_key not in indexed
        indexed[trial_key] = float(row["recovery"])

    summary_rows = []

    for (channel, loss, method), values in sorted(grouped.items()):
        assert len(values) == 30

        stats = summarize(values)

        summary_rows.append({
            "channel": channel,
            "target_loss_rate": loss,
            "method": method,
            **stats,
        })

    save_csv(SUMMARY, summary_rows)

    paired_rows = []

    for channel in ("iid", "burst"):
        for loss in (0.05, 0.10, 0.25, 0.50, 0.75):
            for parity in (2, 4, 8):
                differences = []

                for seed in range(42, 72):
                    standard = indexed[
                        (channel, loss, seed, f"RS (8+{parity})")
                    ]
                    interleaved = indexed[
                        (
                            channel,
                            loss,
                            seed,
                            f"RS Interleaved (8+{parity})",
                        )
                    ]

                    differences.append(interleaved - standard)

                stats = summarize(differences)

                paired_rows.append({
                    "channel": channel,
                    "target_loss_rate": loss,
                    "parity": parity,
                    **stats,
                })

    save_csv(PAIRED, paired_rows)

    assert len(summary_rows) == 100
    assert len(paired_rows) == 30

    print("SATELLITE BENCHMARK STATISTICAL ANALYSIS")
    print("=" * 65)
    print(f"Experiment records: {len(rows)}")
    print(f"Summary groups:      {len(summary_rows)}")
    print(f"Paired comparisons:  {len(paired_rows)}")

    print("\n25% TARGET LOSS — MEAN RECOVERY")
    print("-" * 65)

    for channel in ("iid", "burst"):
        print(f"\n{channel.upper()}")

        for row in summary_rows:
            if (
                row["channel"] == channel
                and row["target_loss_rate"] == 0.25
            ):
                print(
                    f"{row['method']:25} "
                    f"{row['mean']:6.2f}% "
                    f"95% CI [{row['ci_lower']:.2f}, "
                    f"{row['ci_upper']:.2f}]"
                )

    print("\n25% TARGET LOSS — PAIRED INTERLEAVING GAINS")
    print("-" * 65)

    for row in paired_rows:
        if row["target_loss_rate"] == 0.25:
            print(
                f"{row['channel'].upper():6} "
                f"RS (8+{row['parity']}): "
                f"{row['mean']:+.2f} percentage points "
                f"95% CI [{row['ci_lower']:+.2f}, "
                f"{row['ci_upper']:+.2f}]"
            )

    print(f"\nSummary saved: {SUMMARY}")
    print(f"Paired results: {PAIRED}")
    print("\nSatellite statistical analysis: PASS")


if __name__ == "__main__":
    main()
