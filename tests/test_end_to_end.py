from recovery import rs_encode_group, rs_decode_group
from fountain import encode as fountain_encode
from fountain import decode as fountain_decode
from burst_experiment import (
    interleave_rs_groups,
    deinterleave_rs_packets,
)


def test_rs_interleaved_end_to_end_recovery():
    # Three groups, each containing eight source packets.
    original_groups = [
        [
            bytes([(group * 8 + packet) % 256]) * 256
            for packet in range(8)
        ]
        for group in range(3)
    ]

    # Encode each group with two parity packets.
    encoded_groups = [
        rs_encode_group(group, parity_count=2)
        for group in original_groups
    ]

    # Interleave all encoded packets.
    transmitted, positions = interleave_rs_groups(
        encoded_groups
    )

    # Simulate three consecutive packet losses.
    received = transmitted.copy()
    received[3:6] = [None, None, None]

    # Restore original RS group positions.
    restored = deinterleave_rs_packets(
        received,
        positions,
        group_count=3,
        group_length=10,
    )

    # Decode and compare every source packet.
    for original, received_group in zip(
        original_groups, restored
    ):
        result = rs_decode_group(
            received_group,
            data_count=8,
            parity_count=2,
        )

        assert result.success
        assert result.recovered == original


def test_rs_without_interleaving_fails_on_same_burst():
    original_groups = [
        [
            bytes([(group * 8 + packet) % 256]) * 256
            for packet in range(8)
        ]
        for group in range(3)
    ]

    encoded_groups = [
        rs_encode_group(group, parity_count=2)
        for group in original_groups
    ]

    # Transmit groups sequentially, without interleaving.
    transmitted = [
        packet
        for group in encoded_groups
        for packet in group
    ]

    # Same burst length and transmission positions.
    received = transmitted.copy()
    received[3:6] = [None, None, None]

    first_group = received[:10]

    result = rs_decode_group(
        first_group,
        data_count=8,
        parity_count=2,
    )

    # Three erasures exceed the group's two-parity capacity.
    assert not result.success
    assert result.recovered != original_groups[0]




def test_fountain_end_to_end_recovery():
    # Create eight distinct source packets.
    original = [
        bytes([i + 1]) * 256
        for i in range(8)
    ]

    # Generate redundant Fountain symbols.
    encoded = fountain_encode(
        original,
        output_count=80,
        seed=42,
    )

    # Simulate a burst of three consecutive lost symbols.
    received = [
        symbol
        for index, symbol in enumerate(encoded)
        if index not in {3, 4, 5}
    ]

    # Decode received symbols.
    recovered = fountain_decode(
        received,
        source_count=len(original),
    )

    # Verify every recovered packet byte-for-byte.
    assert recovered == original