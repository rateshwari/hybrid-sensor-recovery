"""Evaluate image quality after satellite packet recovery."""

import csv
import math
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

IMAGE_PATH = "data/satellite/raw/satellite_000.png"
OUTPUT_DIR = Path("results/satellite/quality")
SEED = 42
LOSS_RATE = 0.25


def evaluate(source, original, dimensions, padding, result):
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

    return recovered_image, {
        "method": result["method"],
        "transmitted": result["transmitted"],
        "received": result["received"],
        "actual_loss": result["actual_loss"],
        "exact_packets": result["exact"],
        "packet_recovery_percent": result["recovery"],
        "missing_packet_percent": missing_packet_percentage(packets),
        **quality,
    }


def main():
    dimensions, raw = load_satellite_image(IMAGE_PATH)
    source, padding = packetize_image(raw)

    original = Image.frombytes("RGB", dimensions, raw)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    for channel in ("iid", "burst"):
        channel_dir = OUTPUT_DIR / channel
        channel_dir.mkdir(exist_ok=True)

        results = []

        results.append(
            run_method(
                source, channel, "No ECC",
                seed=SEED,
                loss_rate=LOSS_RATE,
                return_packets=True,
            )
        )

        for parity in (2, 4, 8):
            for interleaved in (False, True):
                method = (
                    f"RS Interleaved (8+{parity})"
                    if interleaved
                    else f"RS (8+{parity})"
                )

                results.append(
                    run_method(
                        source, channel, method,
                        parity_count=parity,
                        seed=SEED,
                        loss_rate=LOSS_RATE,
                        return_packets=True,
                    )
                )

        for overhead in (1.25, 1.50, 2.00):
            results.append(
                run_fountain(
                    source, channel, overhead,
                    seed=SEED,
                    loss_rate=LOSS_RATE,
                    return_packets=True,
                )
            )

        assert len(results) == 10

        print(f"\n{channel.upper()} CHANNEL")
        print("-" * 75)

        for result in results:
            recovered_image, metrics = evaluate(
                source, original, dimensions, padding, result
            )

            filename = (
                result["method"]
                .lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("+", "_")
                .replace(".", "_")
                + ".png"
            )

            recovered_image.save(channel_dir / filename)

            records.append({
                "image_path": IMAGE_PATH,
                "channel": channel,
                "seed": SEED,
                "target_loss_rate": LOSS_RATE,
                **metrics,
            })

            psnr_text = (
                "inf"
                if math.isinf(metrics["psnr_db"])
                else f"{metrics['psnr_db']:.2f}"
            )

            print(
                f"{metrics['method']:25} "
                f"Recovery={metrics['packet_recovery_percent']:6.2f}% "
                f"PSNR={psnr_text:>6} dB "
                f"SSIM={metrics['ssim']:.4f}"
            )

    output_csv = OUTPUT_DIR / "quality_results.csv"

    with output_csv.open("w", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=list(records[0])
        )
        writer.writeheader()
        writer.writerows(records)

    assert len(records) == 20

    print(f"\nResults saved: {output_csv}")
    print("Step 137: PASS")


if __name__ == "__main__":
    main()
