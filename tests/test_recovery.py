import pytest

from src.recovery import no_ecc, rs_decode_group, rs_encode_group


def make_packets(count=8, size=32):
    return [
        bytes((i * 17 + j * 3) % 256 for j in range(size))
        for i in range(count)
    ]


def test_rs_recovers_two_missing_data_packets():
    original = make_packets()
    encoded = rs_encode_group(original, parity_count=2)

    received = list(encoded)
    received[1] = None
    received[5] = None

    result = rs_decode_group(received, data_count=8, parity_count=2)

    assert result.success
    assert result.recovered_count == 2
    assert result.recovered == original


def test_rs_fails_cleanly_when_too_many_packets_are_missing():
    original = make_packets()
    encoded = rs_encode_group(original, parity_count=2)

    received = list(encoded)
    received[0] = None
    received[1] = None
    received[2] = None

    result = rs_decode_group(received, data_count=8, parity_count=2)

    assert not result.success
    assert "exceeds" in result.reason


def test_no_ecc_does_not_recover_missing_packets():
    original = make_packets()
    damaged = list(original)
    damaged[3] = None

    result = no_ecc(damaged)

    assert not result.success
    assert result.recovered[3] is None
    assert result.recovered_count == 0


def test_rs_rejects_inconsistent_packet_sizes():
    with pytest.raises(ValueError, match="same length"):
        rs_encode_group([b"abcd", b"abc"], parity_count=1)
