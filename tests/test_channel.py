import pytest

from src.data_pipeline import packetize
from src.channel import (
    burst_bit_errors,
    burst_packet_loss,
    random_bit_errors,
    random_packet_loss,
)


def test_random_packet_loss_is_reproducible():
    packets = packetize(bytes(range(256)) * 4, payload_size=64)

    first = random_packet_loss(packets, 0.25, seed=7)
    second = random_packet_loss(packets, 0.25, seed=7)

    assert first.lost_sequences == second.lost_sequences
    assert len(first.received) + len(first.lost_sequences) == len(packets)


def test_bit_errors_are_detected_by_crc():
    packets = packetize(b"A" * 4096, payload_size=128)

    result = random_bit_errors(
        packets,
        bit_error_probability=0.01,
        seed=7,
    )

    assert result.corrupted_sequences
    assert any(not packet.valid for packet in result.received)


def test_burst_packet_loss_preserves_sequence_ids():
    packets = packetize(b"A" * 4096, payload_size=32)

    result = burst_packet_loss(
        packets,
        good_to_bad=0.2,
        bad_to_good=0.2,
        seed=7,
    )

    assert len(result.received) + len(result.lost_sequences) == len(packets)
    assert result.lost_sequences == sorted(result.lost_sequences)


def test_burst_bit_errors_modify_payloads():
    packets = packetize(b"A" * 4096, payload_size=128)

    result = burst_bit_errors(
        packets,
        burst_probability=0.1,
        mean_burst_bits=8,
        seed=7,
    )

    assert result.corrupted_sequences
    assert any(not packet.valid for packet in result.received)


def test_invalid_loss_probability_is_rejected():
    packets = packetize(b"test")

    with pytest.raises(ValueError):
        random_packet_loss(packets, 1.5)
