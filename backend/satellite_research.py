"""Read precomputed satellite research results for the dashboard."""

import csv
import math
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/satellite"

FILES = {
    "packet_recovery": RESULTS / "benchmark_summary.csv",
    "packet_interleaving": RESULTS / "interleaving_analysis.csv",
    "method_quality": RESULTS / "quality/method_quality_summary.csv",
    "class_quality": RESULTS / "quality/class_quality_summary.csv",
    "ssim_interleaving": RESULTS / "quality/interleaving_ssim_ci.csv",
}

INTEGER_FIELDS = {
    "n",
    "parity",
    "observations",
    "seeds",
    "images_per_seed",
}

NUMERIC_FIELDS = {
    "target_loss_rate",
    "mean",
    "std",
    "ci_lower",
    "ci_upper",
    "mean_ssim",
    "exact_image_recovery_percent",
    "mean_ssim_gain",
    "std_across_seeds",
}


@lru_cache(maxsize=1)
def load_results():
    """Load the five small summary tables once per backend process."""
    results = {}

    for name, path in FILES.items():
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing satellite research summary: {path.name}"
            )

        with path.open(newline="") as file:
            reader = csv.DictReader(file)
            rows = []

            for row in reader:
                cleaned = {}

                for key, value in row.items():
                    if key in INTEGER_FIELDS:
                        cleaned[key] = int(value)
                    elif key in NUMERIC_FIELDS:
                        number = float(value)

                        if not math.isfinite(number):
                            raise ValueError(
                                f"Non-finite {key} in {path.name}"
                            )

                        cleaned[key] = number
                    else:
                        cleaned[key] = value

                rows.append(cleaned)

        results[name] = rows

    return results


def satellite_research_results(
    channel=None,
    method=None,
    loss_rate=None,
    class_name=None,
):
    if channel is not None and channel not in ("iid", "burst"):
        raise ValueError("channel must be iid or burst.")

    data = load_results()

    def matches(row):
        if channel is not None and row.get("channel") != channel:
            return False

        if method is not None and "method" in row:
            if row["method"] != method:
                return False

        if loss_rate is not None and "target_loss_rate" in row:
            if not math.isclose(
                row["target_loss_rate"],
                loss_rate,
                abs_tol=1e-9,
            ):
                return False

        if class_name is not None and "class_name" in row:
            if row["class_name"] != class_name:
                return False

        if method is not None and "parity" in row:
            expected = (
                f"RS Interleaved (8+{row['parity']})"
            )

            if method != expected:
                return False

        return True

    filtered = {
        name: [
            row for row in rows
            if matches(row)
        ]
        for name, rows in data.items()
    }

    return {
        "filters": {
            "channel": channel,
            "method": method,
            "loss_rate": loss_rate,
            "class_name": class_name,
        },
        "metadata": {
            "dataset": "EuroSAT RGB",
            "images": 500,
            "land_use_classes": 10,
            "channel_seeds": 30,
            "packet_benchmark_trials": 3000,
            "image_quality_observations": 300000,
            "packet_size_bytes": 256,
            "source_packets_per_image": 48,
            "note": (
                "Image-quality observations reuse channel recovery "
                "masks across images. They are not 300000 independent "
                "channel trials."
            ),
        },
        **filtered,
    }
