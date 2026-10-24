"""Repeated satellite packet-recovery benchmark."""

import csv
import time
from pathlib import Path

from src.satellite_pipeline import load_satellite_image, packetize_image
from src.satellite_channel_demo import run_method, run_fountain

IMAGE = "data/satellite/raw/satellite_000.png"
OUTPUT = Path("results/satellite/benchmark_results.csv")

SEEDS = range(42, 72)
LOSS_RATES = (0.05, 0.10, 0.25, 0.50, 0.75)
CHANNELS = ("iid", "burst")


def run_all_methods(source, channel, seed, loss_rate):
    yield run_method(
        source, channel, "No ECC",
        seed=seed, loss_rate=loss_rate,
    )

    for parity in (2, 4, 8):
        for interleaved in (False, True):
            name = (
                f"RS Interleaved (8+{parity})"
                if interleaved
                else f"RS (8+{parity})"
            )

            yield run_method(
                source, channel, name,
                parity_count=parity,
                seed=seed,
                loss_rate=loss_rate,
            )

    for overhead in (1.25, 1.50, 2.00):
        yield run_fountain(
            source, channel, overhead,
            seed=seed,
            loss_rate=loss_rate,
        )


def main():
    dimensions, raw = load_satellite_image(IMAGE)
    source, padding = packetize_image(raw)

    assert dimensions == (64, 64)
    assert len(source) == 48
    assert padding == 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "image_path",
        "channel",
        "seed",
        "target_loss_rate",
        "method",
        "transmitted",
        "received",
        "actual_loss",
        "exact",
        "recovery",
    ]

    start = time.perf_counter()
    total = 0

    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for channel in CHANNELS:
            for loss_rate in LOSS_RATES:
                for seed in SEEDS:
                    results = list(
                        run_all_methods(
                            source, channel, seed, loss_rate
                        )
                    )

                    assert len(results) == 10
                    assert len({r["method"] for r in results}) == 10

                    for parity in (2, 4, 8):
                        standard = next(
                            r for r in results
                            if r["method"] == f"RS (8+{parity})"
                        )
                        interleaved = next(
                            r for r in results
                            if r["method"] ==
                            f"RS Interleaved (8+{parity})"
                        )

                        assert (
                            standard["transmitted"]
                            == interleaved["transmitted"]
                        )
                        assert (
                            standard["received"]
                            == interleaved["received"]
                        )

                    for result in results:
                        assert 0 <= result["exact"] <= len(source)
                        assert 0 <= result["actual_loss"] <= 100
                        assert 0 <= result["recovery"] <= 100

                        writer.writerow({
                            "image_path": IMAGE,
                            "channel": channel,
                            "seed": seed,
                            "target_loss_rate": loss_rate,
                            **result,
                        })
                        total += 1

                file.flush()
                print(
                    f"Completed: {channel.upper()} | "
                    f"target loss {loss_rate:.0%} | "
                    f"records {total}",
                    flush=True,
                )

    assert total == 3000

    elapsed = time.perf_counter() - start

    print("\nSATELLITE BENCHMARK SUMMARY")
    print("=" * 48)
    print(f"Methods:            10")
    print(f"Channels:           2")
    print(f"Loss rates:         5")
    print(f"Seeds:              30")
    print(f"Experiment records: {total}")
    print(f"Elapsed time:       {elapsed:.2f} seconds")
    print(f"Results:            {OUTPUT}")
    print("\nSatellite benchmark: PASS")


if __name__ == "__main__":
    main()
