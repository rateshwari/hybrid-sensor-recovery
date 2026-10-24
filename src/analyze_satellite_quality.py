"""Analyze full satellite image-quality results."""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

INPUT = Path("results/satellite/quality/full_quality_results.csv")
OUTPUT = Path("results/satellite/quality")


def save_csv(name, rows):
    path = OUTPUT / name
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def main():
    method_groups = defaultdict(list)
    class_groups = defaultdict(list)
    indexed = {}

    count = 0

    with INPUT.open(newline="") as file:
        for row in csv.DictReader(file):
            count += 1

            channel = row["channel"]
            method = row["method"]
            class_name = row["class_name"]
            image_path = row["image_path"]
            seed = int(row["seed"])

            ssim = float(row["ssim"])
            exact = row["exact_image_recovery"] == "True"

            method_groups[(channel, method)].append((ssim, exact))
            class_groups[(channel, class_name, method)].append(ssim)

            indexed[(image_path, channel, seed, method)] = ssim

    assert count == 300000

    method_rows = []

    for (channel, method), values in sorted(method_groups.items()):
        method_rows.append({
            "channel": channel,
            "method": method,
            "observations": len(values),
            "mean_ssim": mean(v[0] for v in values),
            "exact_image_recovery_percent": (
                sum(v[1] for v in values) / len(values) * 100
            ),
        })

    class_rows = []

    for (channel, class_name, method), values in sorted(class_groups.items()):
        class_rows.append({
            "channel": channel,
            "class_name": class_name,
            "method": method,
            "observations": len(values),
            "mean_ssim": mean(values),
        })

    paired_rows = []

    for channel in ("iid", "burst"):
        for parity in (2, 4, 8):
            standard = f"RS (8+{parity})"
            interleaved = f"RS Interleaved (8+{parity})"

            differences = []

            for image_path, ch, seed, method in indexed:
                if ch != channel or method != standard:
                    continue

                key = (image_path, channel, seed, interleaved)
                differences.append(
                    indexed[key] -
                    indexed[(image_path, channel, seed, standard)]
                )

            paired_rows.append({
                "channel": channel,
                "parity": parity,
                "paired_observations": len(differences),
                "mean_ssim_gain": mean(differences),
            })

    assert len(method_rows) == 20
    assert len(class_rows) == 200
    assert len(paired_rows) == 6
    assert all(r["paired_observations"] == 15000 for r in paired_rows)

    save_csv("method_quality_summary.csv", method_rows)
    save_csv("class_quality_summary.csv", class_rows)
    save_csv("interleaving_quality_summary.csv", paired_rows)

    print("FULL SATELLITE QUALITY ANALYSIS")
    print("=" * 65)
    print(f"Observations:       {count:,}")
    print(f"Method summaries:   {len(method_rows)}")
    print(f"Class summaries:    {len(class_rows)}")
    print(f"Paired comparisons: {len(paired_rows)}")

    print("\nMEAN SSIM AND EXACT IMAGE RECOVERY")
    print("-" * 65)

    for channel in ("iid", "burst"):
        print(f"\n{channel.upper()}")

        for row in method_rows:
            if row["channel"] == channel:
                print(
                    f"{row['method']:25} "
                    f"SSIM={row['mean_ssim']:.4f} "
                    f"Exact={row['exact_image_recovery_percent']:.2f}%"
                )

    print("\nPAIRED INTERLEAVING SSIM GAINS")
    print("-" * 65)

    for row in paired_rows:
        print(
            f"{row['channel'].upper():6} "
            f"RS (8+{row['parity']}): "
            f"{row['mean_ssim_gain']:+.4f}"
        )

    print("\nStep 145: PASS")


if __name__ == "__main__":
    main()
