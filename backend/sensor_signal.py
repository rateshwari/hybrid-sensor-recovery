"""Map real sensor readings to exact packet recovery states."""

from functools import lru_cache
import math

import pandas as pd

from backend.packet_trace import packet_trace
from src.burst_experiment import DATA_PATH, PACKET_SIZE


BYTES_PER_READING = 4
READINGS_PER_PACKET = PACKET_SIZE // BYTES_PER_READING


@lru_cache(maxsize=1)
def load_sensor_data():
    df = pd.read_csv(DATA_PATH)

    required = {"timestamp", "temperature", "humidity"}
    if not required.issubset(df.columns):
        raise ValueError("Sensor dataset is missing required columns.")

    return df


def sensor_signal(
    seed: int,
    loss_rate: float,
    parity_count: int,
    interleaved: bool,
    signal: str,
    start: int = 0,
    count: int = 512,
):
    if signal not in ("temperature", "humidity"):
        raise ValueError("signal must be temperature or humidity.")

    df = load_sensor_data()

    if start < 0 or start >= len(df):
        raise ValueError("start is outside the dataset.")

    if count < 1 or count > 2048:
        raise ValueError("count must be between 1 and 2048.")

    trace = packet_trace(
        seed=seed,
        loss_rate=loss_rate,
        parity_count=parity_count,
        interleaved=interleaved,
    )

    end = min(start + count, len(df))
    points = []

    for reading_index in range(start, end):
        packet_index = reading_index // READINGS_PER_PACKET
        status = trace["packet_statuses"][packet_index]

        original = float(df.iloc[reading_index][signal])

        if not math.isfinite(original):
            raise ValueError("Non-finite sensor reading encountered.")

        points.append({
            "reading_index": reading_index,
            "timestamp": str(df.iloc[reading_index]["timestamp"]),
            "packet_index": packet_index,
            "packet_status": status,
            "original": original,
            "available_after_recovery": (
                None if status == "unrecovered" else original
            ),
        })

    return {
        "method": trace["method"],
        "signal": signal,
        "seed": seed,
        "target_loss_rate": loss_rate,
        "start": start,
        "count": len(points),
        "total_readings": len(df),
        "points": points,
    }
