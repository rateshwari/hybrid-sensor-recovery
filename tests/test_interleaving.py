from burst_experiment import (
    interleave_rs_groups,
    deinterleave_rs_packets,
)


def test_interleaving_preserves_all_packets():
    groups = [
        [b"A0", b"A1", b"A2"],
        [b"B0", b"B1", b"B2"],
        [b"C0", b"C1", b"C2"],
    ]

    transmitted, positions = interleave_rs_groups(groups)

    assert transmitted == [
        b"A0", b"B0", b"C0",
        b"A1", b"B1", b"C1",
        b"A2", b"B2", b"C2",
    ]

    assert len(transmitted) == 9
    assert len(positions) == 9


def test_interleaving_round_trip():
    groups = [
        [b"A0", b"A1", b"A2"],
        [b"B0", b"B1", b"B2"],
        [b"C0", b"C1", b"C2"],
    ]

    transmitted, positions = interleave_rs_groups(groups)

    restored = deinterleave_rs_packets(
        transmitted,
        positions,
        group_count=3,
        group_length=3,
    )

    assert restored == groups


def test_deinterleaving_preserves_missing_packets():
    groups = [
        [b"A0", b"A1", b"A2"],
        [b"B0", b"B1", b"B2"],
        [b"C0", b"C1", b"C2"],
    ]

    transmitted, positions = interleave_rs_groups(groups)

    received = transmitted.copy()

    # Simulate three consecutive lost transmitted packets.
    received[2:5] = [None, None, None]

    restored = deinterleave_rs_packets(
        received,
        positions,
        group_count=3,
        group_length=3,
    )

    assert restored == [
        [b"A0", None, b"A2"],
        [b"B0", None, b"B2"],
        [None, b"C1", b"C2"],
    ]


def test_empty_interleaving():
    transmitted, positions = interleave_rs_groups([])

    assert transmitted == []
    assert positions == []
