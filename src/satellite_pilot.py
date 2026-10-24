"""Small multi-image satellite recovery pilot."""

import csv
import time
from pathlib import Path

from src.satellite_pipeline import load_satellite_image, packetize_image
from src.satellite_channel_demo import run_method, run_fountain

MANIFEST = Path("data/satellite/manifest.csv")


def main():
    with MANIFEST.open(newline="") as file:
        records = list(csv.DictReader(file))

    # Select one image from each class.
    selected = {}
    for record in records:
        selected.setdefault(record["class_name"], record)

    assert len(selected) == 10

    results = []
    start = time.perf_counter()

    for class_name, record in selected.items():
        _, raw = load_satellite_image(record["saved_path"])
        source, padding = packetize_image(raw)

        assert len(source) == 48
        assert padding == 0

        for channel in ("iid", "burst"):
            methods = [
                run_method(source, channel, "No ECC"),
            ]

            for parity in (2, 4, 8):
                methods.append(
                    run_method(
                        source,
                        channel,
                        f"RS (8+{parity})",
                        parity_count=parity,
                    )
                )
                methods.append(
                    run_method(
                        source,
                        channel,
                        f"RS Interleaved (8+{parity})",
                        parity_count=parity,
                    )
                )

            for overhead in (1.25, 1.50, 2.00):
                methods.append(
                    run_fountain(source, channel, overhead)
                )

            assert len(methods) == 10

            for result in methods:
                results.append({
                    "class_name": class_name,
                    "image_path": record["saved_path"],
                    "channel": channel,
                    **result,
                })

        print(f"Completed: {class_name}", flush=True)

    elapsed = time.perf_counter() - start

    output = Path("results/satellite/pilot_results.csv")
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys()),
        )
        writer.writeheader()
        writer.writerows(results)

    assert len(results) == 200

    print("\nSATELLITE PILOT SUMMARY")
    print("=" * 45)
    print(f"Images tested:      {len(selected)}")
    print("Methods:            10")
    print("Channels:           2")
    print(f"Experiment records: {len(results)}")
    print(f"Elapsed time:       {elapsed:.2f} seconds")
    print(f"Results saved:      {output}")
    print("\nSatellite pilot: PASS")


if __name__ == "__main__":
    main()
