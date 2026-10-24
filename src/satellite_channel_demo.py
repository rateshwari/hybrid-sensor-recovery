"""Satellite-image packet recovery under IID and burst erasures."""

import random

from src.satellite_pipeline import (
    load_satellite_image,
    packetize_image,
    count_exact_packets,
)
from src.recovery import rs_encode_group, rs_decode_group
from src.burst_experiment import (
    burst_erase_packets,
    interleave_rs_groups,
    deinterleave_rs_packets,
)

IMAGE = "data/satellite/raw/satellite_000.png"
SEED = 42
LOSS_RATE = 0.25
DATA_COUNT = 8
PARITY_COUNT = 4


def erase(packets, channel, seed, loss_rate):
    """Apply reproducible erasures to transmission slots."""
    if channel == "burst":
        return burst_erase_packets(packets, seed, loss_rate)

    if channel == "iid":
        rng = random.Random(seed)
        return [
            None if rng.random() < loss_rate else packet
            for packet in packets
        ]

    raise ValueError(f"Unknown channel: {channel}")


def run_method(source, channel, method, parity_count=4, seed=SEED, loss_rate=LOSS_RATE, return_packets=False):
    if method == "No ECC":
        received = erase(source, channel, seed, loss_rate)
        restored = received
        transmitted_count = len(source)
        received_count = sum(p is not None for p in received)

    else:
        groups = [
            source[i:i + DATA_COUNT]
            for i in range(0, len(source), DATA_COUNT)
        ]

        assert all(len(g) == DATA_COUNT for g in groups)

        encoded_groups = [
            rs_encode_group(group, parity_count)
            for group in groups
        ]

        if method.startswith("RS Interleaved"):
            transmitted, positions = interleave_rs_groups(
                encoded_groups
            )

            received = erase(
                transmitted, channel, seed, loss_rate
            )

            received_groups = deinterleave_rs_packets(
                received,
                positions,
                len(groups),
                DATA_COUNT + parity_count,
            )

        elif method.startswith("RS ("):
            # Match the sensor experiment's noninterleaved order:
            # all source packets first, followed by parity packets.
            transmitted = [
                packet
                for group in encoded_groups
                for packet in group[:DATA_COUNT]
            ] + [
                packet
                for group in encoded_groups
                for packet in group[DATA_COUNT:]
            ]

            received = erase(
                transmitted, channel, seed, loss_rate
            )

            source_received = received[:len(source)]
            parity_received = received[len(source):]

            received_groups = [
                source_received[
                    i * DATA_COUNT:(i + 1) * DATA_COUNT
                ] + parity_received[
                    i * parity_count:(i + 1) * parity_count
                ]
                for i in range(len(groups))
            ]

        else:
            raise ValueError(f"Unknown method: {method}")

        transmitted_count = len(transmitted)
        received_count = sum(p is not None for p in received)

        restored = []

        for group in received_groups:
            result = rs_decode_group(
                group,
                DATA_COUNT,
                parity_count,
            )
            restored.extend(result.recovered)

    exact = count_exact_packets(source, restored)

    metrics = {
        "method": method,
        "transmitted": transmitted_count,
        "received": received_count,
        "actual_loss": (
            (transmitted_count - received_count)
            / transmitted_count * 100
        ),
        "exact": exact,
        "recovery": exact / len(source) * 100,
    }

    if return_packets:
        metrics["restored_packets"] = restored

    return metrics


def main():
    _, raw = load_satellite_image(IMAGE)
    source, padding = packetize_image(raw)

    assert len(source) == 48
    assert padding == 0

    methods = [
        "No ECC",
        "RS (8+4)",
        "RS Interleaved (8+4)",
    ]

    for channel in ("iid", "burst"):
        print(f"\nCHANNEL: {channel.upper()}")
        print(
            f"{'Method':25} {'Tx':>5} {'Loss %':>9} "
            f"{'Exact':>8} {'Recovery %':>12}"
        )
        print("-" * 67)

        for method in methods:
            result = run_method(source, channel, method)

            print(
                f"{method:25} "
                f"{result['transmitted']:5} "
                f"{result['actual_loss']:9.2f} "
                f"{result['exact']:5}/48 "
                f"{result['recovery']:11.2f}%"
            )


if __name__ == "__main__":
    main()


def run_fountain(source, channel, overhead, seed=SEED, loss_rate=LOSS_RATE, return_packets=False):
    """Evaluate Fountain recovery using the sensor experiment's block settings."""
    import math
    from src.fountain import encode as fountain_encode
    from src.fountain import decode as fountain_decode

    block_size = 32
    blocks = [
        source[i:i + block_size]
        for i in range(0, len(source), block_size)
    ]

    encoded_blocks = []

    for block_index, block in enumerate(blocks):
        output_count = max(
            len(block),
            math.ceil(len(block) * overhead),
        )

        symbols = fountain_encode(
            block,
            output_count=output_count,
            seed=seed + block_index * 1009,
        )

        encoded_blocks.append(symbols)

    transmitted = [
        symbol
        for block in encoded_blocks
        for symbol in block
    ]

    # Preserve the distinct Fountain channel stream used in sensor trials.
    received = erase(
        transmitted,
        channel,
        seed + 500_009,
        loss_rate,
    )

    restored = []
    cursor = 0

    for block, symbols in zip(blocks, encoded_blocks):
        block_received = received[
            cursor:cursor + len(symbols)
        ]
        cursor += len(symbols)

        surviving = [
            symbol for symbol in block_received
            if symbol is not None
        ]

        decoded = fountain_decode(
            surviving,
            source_count=len(block),
        )

        restored.extend(decoded)

    exact = count_exact_packets(source, restored)
    received_count = sum(symbol is not None for symbol in received)

    metrics = {
        "method": f"Fountain ({overhead:.2f}x)",
        "transmitted": len(transmitted),
        "received": received_count,
        "actual_loss": (
            (len(transmitted) - received_count)
            / len(transmitted) * 100
        ),
        "exact": exact,
        "recovery": exact / len(source) * 100,
    }

    if return_packets:
        metrics["restored_packets"] = restored

    return metrics
