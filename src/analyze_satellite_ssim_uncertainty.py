"""Seed-level uncertainty for paired satellite SSIM gains."""

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

INPUT = Path("results/satellite/quality/full_quality_results.csv")
OUTPUT = Path("results/satellite/quality/interleaving_ssim_ci.csv")

T_CRITICAL = 2.04523  # Two-sided 95%, 29 degrees of freedom


def main():
    # Store paired SSIM values for each image, channel, seed and method.
    indexed = {}

    with INPUT.open(newline="") as file:
        for row in csv.DictReader(file):
            key = (
                row["image_path"],
                row["channel"],
                int(row["seed"]),
                row["method"],
            )

            assert key not in indexed
            indexed[key] = float(row["ssim"])

    assert len(indexed) == 300000

    results = []

    for channel in ("iid", "burst"):
        for parity in (2, 4, 8):
            standard = f"RS (8+{parity})"
            interleaved = f"RS Interleaved (8+{parity})"

            per_seed = defaultdict(list)

            for image_path, ch, seed, method in indexed:
                if ch != channel or method != standard:
                    continue

                standard_ssim = indexed[
                    (image_path, channel, seed, standard)
                ]
                interleaved_ssim = indexed[
                    (image_path, channel, seed, interleaved)
                ]

                per_seed[seed].append(
                    interleaved_ssim - standard_ssim
                )

            assert len(per_seed) == 30
            assert all(len(values) == 500 for values in per_seed.values())

            seed_means = [
                mean(per_seed[seed])
                for seed in sorted(per_seed)
            ]

            avg = mean(seed_means)
            sd = stdev(seed_means)
            margin = T_CRITICAL * sd / math.sqrt(len(seed_means))

            results.append({
                "channel": channel,
                "parity": parity,
                "seeds": len(seed_means),
                "images_per_seed": 500,
                "mean_ssim_gain": avg,
                "std_across_seeds": sd,
                "ci_lower": avg - margin,
                "ci_upper": avg + margin,
            })

    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=list(results[0])
        )
        writer.writeheader()
        writer.writerows(results)

    print("PAIRED SATELLITE SSIM ANALYSIS")
    print("=" * 65)

    for row in results:
        print(
            f"{row['channel'].upper():6} "
            f"RS (8+{row['parity']}): "
            f"Gain={row['mean_ssim_gain']:+.4f} "
            f"95% CI [{row['ci_lower']:+.4f}, "
            f"{row['ci_upper']:+.4f}]"
        )

    print(f"\nOutput: {OUTPUT}")
    print("Step 146: PASS")


if __name__ == "__main__":
    main()
