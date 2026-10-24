"""Lossless RGB satellite-image packetization and reconstruction."""

from pathlib import Path
from PIL import Image

PACKET_SIZE = 256


def load_satellite_image(path: str | Path):
    """Load an RGB image and return its dimensions and raw pixel bytes."""
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return rgb.size, rgb.tobytes()


def packetize_image(raw: bytes, packet_size: int = PACKET_SIZE):
    """Split image bytes into equal-sized source packets."""
    if packet_size <= 0:
        raise ValueError("Packet size must be positive")

    padding = (-len(raw)) % packet_size
    padded = raw + bytes(padding)

    packets = [
        padded[i:i + packet_size]
        for i in range(0, len(padded), packet_size)
    ]

    return packets, padding


def reconstruct_image(
    packets: list[bytes | None],
    dimensions: tuple[int, int],
    padding: int = 0,
):
    """Reconstruct RGB image; display unrecovered bytes as black."""
    if not packets:
        raise ValueError("No packets supplied")

    surviving = next(
        (packet for packet in packets if packet is not None),
        None,
    )

    packet_size = len(surviving) if surviving is not None else 256

    restored = b"".join(
        packet if packet is not None else bytes(packet_size)
        for packet in packets
    )

    if padding:
        restored = restored[:-padding]

    expected_size = dimensions[0] * dimensions[1] * 3

    if len(restored) != expected_size:
        raise ValueError(
            f"Expected {expected_size} image bytes, got {len(restored)}"
        )

    return Image.frombytes("RGB", dimensions, restored)


def count_exact_packets(
    original: list[bytes],
    recovered: list[bytes | None],
):
    """Count packets recovered exactly, including originally received ones."""
    if len(original) != len(recovered):
        raise ValueError("Packet counts do not match")

    return sum(
        actual is not None and actual == expected
        for expected, actual in zip(original, recovered)
    )
