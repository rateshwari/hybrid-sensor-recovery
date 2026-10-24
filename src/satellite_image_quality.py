"""Image-quality metrics for satellite packet recovery."""

import warnings

import numpy as np
from PIL import Image
from skimage.metrics import (
    peak_signal_noise_ratio,
    structural_similarity,
)


def calculate_image_quality(original: Image.Image, recovered: Image.Image):
    """Compare two RGB images using pixel-level metrics."""

    original_array = np.asarray(
        original.convert("RGB"), dtype=np.uint8
    )
    recovered_array = np.asarray(
        recovered.convert("RGB"), dtype=np.uint8
    )

    if original_array.shape != recovered_array.shape:
        raise ValueError("Image dimensions must match")

    exact = bool(np.array_equal(original_array, recovered_array))

    if exact:
        psnr = float("inf")
        ssim = 1.0
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)

            psnr = float(
                peak_signal_noise_ratio(
                    original_array,
                    recovered_array,
                    data_range=255,
                )
            )

        ssim = float(
            structural_similarity(
                original_array,
                recovered_array,
                channel_axis=2,
                data_range=255,
            )
        )

    return {
        "psnr_db": psnr,
        "ssim": ssim,
        "exact_image_recovery": exact,
    }


def missing_packet_percentage(recovered_packets):
    """Measure packets still missing after decoding."""
    if not recovered_packets:
        raise ValueError("Packet list cannot be empty")

    missing = sum(
        packet is None for packet in recovered_packets
    )

    return missing / len(recovered_packets) * 100
