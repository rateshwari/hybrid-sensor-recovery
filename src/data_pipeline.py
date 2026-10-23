"""Quantization, serialization, packetization, and integrity checks."""

from dataclasses import dataclass
import struct
import zlib

import numpy as np
import pandas as pd


# Each signal is mapped to the full uint16 range using fixed,
# documented physical ranges.
SIGNAL_RANGES = {
    "temperature": (-40.0, 85.0),
    "humidity": (0.0, 100.0),
}

SIGNAL_NAMES = tuple(SIGNAL_RANGES)


@dataclass(frozen=True)
class Packet:
    sequence: int
    payload: bytes
    crc32: int

    @property
    def valid(self) -> bool:
        return (zlib.crc32(self.payload) & 0xFFFFFFFF) == self.crc32


def quantize(df: pd.DataFrame) -> np.ndarray:
    """Map two sensor signals to uint16 values."""
    values = df[list(SIGNAL_NAMES)].to_numpy(dtype=np.float64)

    if not np.isfinite(values).all():
        raise ValueError("Input contains missing or non-finite values.")

    result = np.empty(values.shape, dtype=np.uint16)

    for column, name in enumerate(SIGNAL_NAMES):
        low, high = SIGNAL_RANGES[name]
        signal = values[:, column]

        if ((signal < low) | (signal > high)).any():
            raise ValueError(f"{name} values fall outside [{low}, {high}].")

        scaled = (signal - low) / (high - low) * 65535.0
        result[:, column] = np.rint(scaled).astype(np.uint16)

    return result


def dequantize(values: np.ndarray) -> pd.DataFrame:
    """Convert uint16 values back to approximate physical readings."""
    values = np.asarray(values)

    if values.ndim != 2 or values.shape[1] != len(SIGNAL_NAMES):
        raise ValueError("Expected an array with two signal columns.")

    if values.dtype != np.uint16:
        raise TypeError("Expected uint16 quantized values.")

    result = {}

    for column, name in enumerate(SIGNAL_NAMES):
        low, high = SIGNAL_RANGES[name]
        result[name] = low + values[:, column].astype(np.float64) / 65535.0 * (
            high - low
        )

    return pd.DataFrame(result)


def serialize(values: np.ndarray) -> bytes:
    """Serialize quantized values in a documented little-endian format."""
    values = np.asarray(values)

    if values.dtype != np.uint16:
        raise TypeError("Expected uint16 values.")

    return values.astype("<u2", copy=False).tobytes(order="C")


def deserialize(data: bytes) -> np.ndarray:
    """Deserialize a complete little-endian uint16 stream."""
    if len(data) % 4 != 0:
        raise ValueError("Byte stream length must be divisible by 4.")

    return np.frombuffer(data, dtype="<u2").reshape(-1, 2).copy()


def packetize(data: bytes, payload_size: int = 256) -> list[Packet]:
    """Split bytes into packets with sequence IDs and CRC32."""
    if payload_size <= 0:
        raise ValueError("payload_size must be positive.")

    packets = []

    for sequence, start in enumerate(range(0, len(data), payload_size)):
        payload = data[start : start + payload_size]
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        packets.append(Packet(sequence, payload, crc))

    return packets


def depacketize(packets: list[Packet]) -> bytes:
    """Validate and reassemble ordered, complete packets."""
    if not packets:
        return b""

    expected_sequences = list(range(len(packets)))
    actual_sequences = [packet.sequence for packet in packets]

    if actual_sequences != expected_sequences:
        raise ValueError("Missing, duplicate, or out-of-order packet.")

    for packet in packets:
        if not packet.valid:
            raise ValueError(f"CRC failure in packet {packet.sequence}.")

    return b"".join(packet.payload for packet in packets)
