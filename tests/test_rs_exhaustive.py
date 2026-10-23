from itertools import combinations

from src.recovery import rs_encode_group, rs_decode_group


DATA_COUNT = 8
PARITY_COUNT = 2
TOTAL_COUNT = DATA_COUNT + PARITY_COUNT


def make_source_packets(size=16):
    """Create deterministic packets with different byte patterns."""
    return [
        bytes((packet_index * 29 + byte_index * 7) % 256
              for byte_index in range(size))
        for packet_index in range(DATA_COUNT)
    ]


def test_all_erasure_patterns_up_to_rs_capacity():
    """All 56 patterns with zero, one, or two erasures must recover."""
    original = make_source_packets()
    encoded = rs_encode_group(original, parity_count=PARITY_COUNT)

    patterns_tested = 0

    for erasure_count in range(PARITY_COUNT + 1):
        for erased_positions in combinations(
            range(TOTAL_COUNT), erasure_count
        ):
            received = list(encoded)

            for position in erased_positions:
                received[position] = None

            result = rs_decode_group(
                received,
                data_count=DATA_COUNT,
                parity_count=PARITY_COUNT,
            )

            assert result.success, (
                f"Decoder failed for erasures {erased_positions}: "
                f"{result.reason}"
            )
            assert result.recovered == original, (
                f"Incorrect reconstruction for erasures {erased_positions}"
            )

            patterns_tested += 1

    assert patterns_tested == 56


def test_three_erasures_are_reported_as_failure():
    """Three known erasures exceed the configured two-parity capacity."""
    original = make_source_packets()
    encoded = rs_encode_group(original, parity_count=PARITY_COUNT)

    received = list(encoded)
    received[0] = None
    received[3] = None
    received[8] = None

    result = rs_decode_group(
        received,
        data_count=DATA_COUNT,
        parity_count=PARITY_COUNT,
    )

    assert not result.success
    assert "exceeds" in result.reason


def test_recovery_does_not_modify_original_packets():
    original = make_source_packets()
    original_copy = list(original)
    encoded = rs_encode_group(original, parity_count=PARITY_COUNT)

    received = list(encoded)
    received[2] = None
    received[9] = None

    rs_decode_group(
        received,
        data_count=DATA_COUNT,
        parity_count=PARITY_COUNT,
    )

    assert original == original_copy
