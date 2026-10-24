"""Optimized satellite image-quality evaluation using recovery masks."""

import argparse
import csv
import math
import time
from pathlib import Path

from PIL import Image

from src.satellite_pipeline import (
    load_satellite_image,
    packetize_image,
    reconstruct_image,
)
from src.satellite_channel_demo import run_method, run_fountain
from src.satellite_image_quality import calculate_image_quality

MANIFEST = Path("data/satellite/manifest.csv")
OUTPUT_DIR = Path("results/satellite/quality")

CHANNELS = ("iid", "burst")
LOSS_RATE = 0.25


def run_all_methods(source, channel, seed):
    yield run_method(
        source, channel, "No ECC",
        seed=seed,
        loss_rate=LOSS_RATE,
        return_packets=True,
    )

    for parity in (2, 4, 8):
        for interleaved in (False, True):
            method = (
                f"RS Interleaved (8+{parity})"
                if interleaved
                else f"RS (8+{parity})"
            )

            yield run_method(
                source, channel, method,
                parity_count=parity,
                seed=seed,
                loss_rate=LOSS_RATE,
                return_packets=True,
            )

    for overhead in (1.25, 1.50, 2.00):
        yield run_fountain(
            source, channel, overhead,
            seed=seed,
            loss_rate=LOSS_RATE,
            return_packets=True,
        )


def create_masks(reference_source, seeds):
    """Generate masks once for each method/channel/seed."""
    configurations = {}

    for channel in CHANNELS:
        for seed in seeds:
            results = list(
                run_all_methods(reference_source, channel, seed)
            )

            assert len(results) == 10

            for result in results:
                packets = result["restored_packets"]

                assert len(packets) == len(reference_source)

                for original, recovered in zip(
                    reference_source, packets
                ):
                    assert recovered is None or recovered == original

                mask = tuple(
                    packet is not None for packet in packets
                )

                configurations[
                    (channel, seed, result["method"])
                ] = {
                    "mask": mask,
                    "transmitted": result["transmitted"],
                    "received": result["received"],
                    "actual_loss": result["actual_loss"],
                    "exact_packets": result["exact"],
                    "packet_recovery_percent": result["recovery"],
                }

    assert len(configurations) == len(CHANNELS) * len(seeds) * 10

    return configurations


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--images", type=int, default=10
    )
    parser.add_argument(
        "--seeds", type=int, default=3
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_DIR / "optimized_test.csv"),
    )

    args = parser.parse_args()

    assert 1 <= args.images <= 500
    assert 1 <= args.seeds <= 30

    with MANIFEST.open(newline="") as file:
        manifest = list(csv.DictReader(file))

    # Round-robin class selection ensures the 10-image
    # validation run contains one image from each class.
    by_class = {}

    for record in manifest:
        by_class.setdefault(record["class_name"], []).append(record)

    assert len(by_class) == 10

    selected = []

    for index in range(50):
        for class_name in sorted(by_class):
            if index < len(by_class[class_name]):
                selected.append(by_class[class_name][index])

    selected = selected[:args.images]

    seeds = tuple(range(42, 42 + args.seeds))

    # Use the first image only to generate packet masks.
    _, reference_raw = load_satellite_image(
        selected[0]["saved_path"]
    )
    reference_source, _ = packetize_image(reference_raw)

    configurations = create_masks(reference_source, seeds)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "image_path",
        "class_name",
        "channel",
        "seed",
        "target_loss_rate",
        "method",
        "transmitted",
        "received",
        "actual_loss",
        "exact_packets",
        "packet_recovery_percent",
        "missing_packet_percent",
        "psnr_db",
        "ssim",
        "exact_image_recovery",
    ]

    start = time.perf_counter()
    count = 0

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for record in selected:
            dimensions, raw = load_satellite_image(
                record["saved_path"]
            )

            source, padding = packetize_image(raw)
            original = Image.frombytes("RGB", dimensions, raw)

            assert len(source) == len(reference_source)
            assert all(
                len(packet) == len(reference_source[0])
                for packet in source
            )

            for (channel, seed, method), config in configurations.items():
                recovered_packets = [
                    packet if keep else None
                    for packet, keep in zip(source, config["mask"])
                ]

                recovered_image = reconstruct_image(
                    recovered_packets, dimensions, padding
                )

                quality = calculate_image_quality(
                    original, recovered_image
                )

                assert quality["exact_image_recovery"] == (
                    config["exact_packets"] == len(source)
                )

                writer.writerow({
                    "image_path": record["saved_path"],
                    "class_name": record["class_name"],
                    "channel": channel,
                    "seed": seed,
                    "target_loss_rate": LOSS_RATE,
                    "method": method,
                    "transmitted": config["transmitted"],
                    "received": config["received"],
                    "actual_loss": config["actual_loss"],
                    "exact_packets": config["exact_packets"],
                    "packet_recovery_percent": config[
                        "packet_recovery_percent"
                    ],
                    "missing_packet_percent": (
                        100 - config["packet_recovery_percent"]
                    ),
                    **quality,
                })

                count += 1

            file.flush()

            print(
                f"Completed {record['class_name']}: "
                f"{count} records",
                flush=True,
            )

    expected = args.images * args.seeds * len(CHANNELS) * 10

    assert count == expected

    elapsed = time.perf_counter() - start

    print("\nOPTIMIZED SATELLITE QUALITY EVALUATION")
    print("=" * 55)
    print(f"Images:         {args.images}")
    print(f"Seeds:          {args.seeds}")
    print(f"Configurations: {len(configurations)}")
    print(f"Records:        {count}")
    print(f"Elapsed:        {elapsed:.2f} seconds")
    print(f"Output:         {output}")
    print("\nOptimized evaluation: PASS")


if __name__ == "__main__":
    main()
