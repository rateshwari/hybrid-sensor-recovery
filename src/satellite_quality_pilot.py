"""Multi-image satellite quality pilot."""

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
from src.satellite_image_quality import (
    calculate_image_quality,
    missing_packet_percentage,
)

MANIFEST = Path("data/satellite/manifest.csv")
OUTPUT = Path("results/satellite/quality/pilot_results.csv")

SEEDS = (42, 43, 44)
CHANNELS = ("iid", "burst")
LOSS_RATE = 0.25


def run_methods(source, channel, seed):
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


def main():
    with MANIFEST.open(newline="") as file:
        manifest = list(csv.DictReader(file))

    # Select the first image from each class.
    selected = {}
    for record in manifest:
        selected.setdefault(record["class_name"], record)

    assert len(selected) == 10

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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

    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for class_name, record in sorted(selected.items()):
            image_path = record["saved_path"]

            dimensions, raw = load_satellite_image(image_path)
            source, padding = packetize_image(raw)
            original = Image.frombytes("RGB", dimensions, raw)

            assert len(source) == 48

            for channel in CHANNELS:
                for seed in SEEDS:
                    results = list(run_methods(source, channel, seed))
                    assert len(results) == 10

                    for result in results:
                        packets = result["restored_packets"]

                        recovered_image = reconstruct_image(
                            packets, dimensions, padding
                        )

                        quality = calculate_image_quality(
                            original, recovered_image
                        )

                        assert quality["exact_image_recovery"] == (
                            result["exact"] == len(source)
                        )

                        missing = missing_packet_percentage(packets)

                        assert abs(
                            result["recovery"] + missing - 100
                        ) < 1e-6

                        writer.writerow({
                            "image_path": image_path,
                            "class_name": class_name,
                            "channel": channel,
                            "seed": seed,
                            "target_loss_rate": LOSS_RATE,
                            "method": result["method"],
                            "transmitted": result["transmitted"],
                            "received": result["received"],
                            "actual_loss": result["actual_loss"],
                            "exact_packets": result["exact"],
                            "packet_recovery_percent": result["recovery"],
                            "missing_packet_percent": missing,
                            **quality,
                        })

                        count += 1

            file.flush()
            print(
                f"Completed {class_name}: {count} records",
                flush=True,
            )

    assert count == 600

    elapsed = time.perf_counter() - start

    print("\nSATELLITE QUALITY PILOT")
    print("=" * 50)
    print(f"Images:       {len(selected)}")
    print(f"Channels:     {len(CHANNELS)}")
    print(f"Seeds:        {len(SEEDS)}")
    print("Methods:      10")
    print(f"Records:      {count}")
    print(f"Elapsed:      {elapsed:.2f} seconds")
    print(f"Output:       {OUTPUT}")
    print("\nStep 140: PASS")


if __name__ == "__main__":
    main()
