"""Satellite-image recovery simulation for the dashboard."""

import base64
import csv
import io
import math
from functools import lru_cache
from pathlib import Path

from src.satellite_pipeline import (
    load_satellite_image,
    packetize_image,
    reconstruct_image,
)
from src.satellite_channel_demo import run_method, run_fountain
from src.satellite_image_quality import calculate_image_quality

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "data/satellite/manifest.csv"

METHODS = (
    "No ECC",
    "RS (8+2)",
    "RS (8+4)",
    "RS (8+8)",
    "RS Interleaved (8+2)",
    "RS Interleaved (8+4)",
    "RS Interleaved (8+8)",
    "Fountain (1.25x)",
    "Fountain (1.50x)",
    "Fountain (2.00x)",
)


@lru_cache(maxsize=1)
def load_manifest():
    with MANIFEST.open(newline="") as file:
        records = list(csv.DictReader(file))

    if not records:
        raise ValueError("Satellite image manifest is empty.")

    return records


def image_to_data_url(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")

    return f"data:image/png;base64,{encoded}"


def satellite_simulation(
    image_index: int,
    channel: str,
    method: str,
    seed: int,
    loss_rate: float,
):
    records = load_manifest()

    if not 0 <= image_index < len(records):
        raise ValueError("image_index is outside the dataset.")

    if channel not in ("iid", "burst"):
        raise ValueError("channel must be iid or burst.")

    if method not in METHODS:
        raise ValueError("Unknown satellite recovery method.")

    if not 0 < loss_rate <= 0.75:
        raise ValueError("loss_rate must be greater than 0 and at most 0.75.")

    record = records[image_index]

    # Resolve only paths listed in our trusted manifest.
    image_path = (
        PROJECT_ROOT / record["saved_path"]
    ).resolve()

    allowed_directory = (
        PROJECT_ROOT / "data/satellite/balanced"
    ).resolve()

    if not image_path.is_relative_to(allowed_directory):
        raise ValueError("Invalid satellite image path.")

    dimensions, raw = load_satellite_image(image_path)
    source_packets, padding = packetize_image(raw)

    if method.startswith("Fountain"):
        overhead = float(
            method.removeprefix("Fountain (")
            .removesuffix("x)")
        )

        result = run_fountain(
            source_packets,
            channel,
            overhead,
            seed=seed,
            loss_rate=loss_rate,
            return_packets=True,
        )
    else:
        parity_count = (
            int(method.split("+")[1].rstrip(")"))
            if method != "No ECC"
            else 4
        )

        result = run_method(
            source_packets,
            channel,
            method,
            parity_count=parity_count,
            seed=seed,
            loss_rate=loss_rate,
            return_packets=True,
        )

    recovered_packets = result["restored_packets"]

    from PIL import Image

    original_image = Image.frombytes(
        "RGB", dimensions, raw
    )

    recovered_image = reconstruct_image(
        recovered_packets,
        dimensions,
        padding,
    )

    quality = calculate_image_quality(
        original_image,
        recovered_image,
    )

    psnr = quality["psnr_db"]

    return {
        "image_index": image_index,
        "class_name": record["class_name"],
        "channel": channel,
        "method": method,
        "seed": seed,
        "target_loss_rate": loss_rate,
        "source_packets": len(source_packets),
        "transmitted_packets": result["transmitted"],
        "received_packets": result["received"],
        "actual_loss_percent": result["actual_loss"],
        "exact_packets": result["exact"],
        "packet_recovery_percent": result["recovery"],
        "redundancy_percent": (
            (result["transmitted"] / len(source_packets) - 1)
            * 100
        ),
        "psnr_db": psnr if math.isfinite(psnr) else None,
        "ssim": quality["ssim"],
        "exact_image_recovery": quality["exact_image_recovery"],
        "original_image": image_to_data_url(original_image),
        "recovered_image": image_to_data_url(recovered_image),
    }
