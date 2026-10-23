"""Reproducible packet-loss and bit-error channel simulations."""

from dataclasses import dataclass
import random

from src.data_pipeline import Packet


@dataclass
class ChannelResult:
    received: list[Packet]
    lost_sequences: list[int]
    corrupted_sequences: list[int]


def random_packet_loss(
    packets: list[Packet],
    loss_probability: float,
    seed: int = 42,
) -> ChannelResult:
    """Independently erase packets with the specified probability."""
    _validate_probability(loss_probability)
    rng = random.Random(seed)

    received = []
    lost = []

    for packet in packets:
        if rng.random() < loss_probability:
            lost.append(packet.sequence)
        else:
            received.append(packet)

    return ChannelResult(received, lost, [])


def burst_packet_loss(
    packets: list[Packet],
    good_to_bad: float = 0.02,
    bad_to_good: float = 0.25,
    seed: int = 42,
) -> ChannelResult:
    """Gilbert-Elliott-style packet erasures.

    GOOD state: packets are received.
    BAD state: packets are lost.
    """
    _validate_probability(good_to_bad)
    _validate_probability(bad_to_good)

    rng = random.Random(seed)
    bad_state = False
    received = []
    lost = []

    for packet in packets:
        if bad_state:
            lost.append(packet.sequence)
            if rng.random() < bad_to_good:
                bad_state = False
        else:
            received.append(packet)
            if rng.random() < good_to_bad:
                bad_state = True

    return ChannelResult(received, lost, [])


def random_bit_errors(
    packets: list[Packet],
    bit_error_probability: float,
    seed: int = 42,
) -> ChannelResult:
    """Flip each transmitted payload bit independently."""
    _validate_probability(bit_error_probability)
    rng = random.Random(seed)

    received = []
    corrupted = []

    for packet in packets:
        payload = bytearray(packet.payload)
        changed = False

        for byte_index in range(len(payload)):
            for bit_index in range(8):
                if rng.random() < bit_error_probability:
                    payload[byte_index] ^= 1 << bit_index
                    changed = True

        received.append(
            Packet(
                sequence=packet.sequence,
                payload=bytes(payload),
                crc32=packet.crc32,
            )
        )

        if changed:
            corrupted.append(packet.sequence)

    return ChannelResult(received, [], corrupted)


def burst_bit_errors(
    packets: list[Packet],
    burst_probability: float = 0.02,
    mean_burst_bits: int = 16,
    seed: int = 42,
) -> ChannelResult:
    """Start occasional bit-error bursts at random payload positions."""
    _validate_probability(burst_probability)

    if mean_burst_bits < 1:
        raise ValueError("mean_burst_bits must be at least 1.")

    rng = random.Random(seed)
    received = []
    corrupted = []

    for packet in packets:
        payload = bytearray(packet.payload)
        changed = False
        total_bits = len(payload) * 8

        for start_bit in range(total_bits):
            if rng.random() < burst_probability:
                # Geometric burst length with the requested approximate mean.
                burst_length = max(
                    1,
                    int(rng.expovariate(1.0 / mean_burst_bits)) + 1,
                )
                end_bit = min(total_bits, start_bit + burst_length)

                for bit in range(start_bit, end_bit):
                    payload[bit // 8] ^= 1 << (bit % 8)

                changed = True

        received.append(
            Packet(
                sequence=packet.sequence,
                payload=bytes(payload),
                crc32=packet.crc32,
            )
        )

        if changed:
            corrupted.append(packet.sequence)

    return ChannelResult(received, [], corrupted)


def _validate_probability(probability: float) -> None:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("Probability must be between 0 and 1.")
