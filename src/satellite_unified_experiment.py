"""Unified satellite packet-recovery demonstration."""

from src.satellite_pipeline import (
    load_satellite_image,
    packetize_image,
)
from src.satellite_channel_demo import (
    run_method,
    run_fountain,
    IMAGE,
    SEED,
    LOSS_RATE,
)


def main():
    dimensions, raw = load_satellite_image(IMAGE)
    source, padding = packetize_image(raw)

    print("SATELLITE RECOVERY EXPERIMENT")
    print("=" * 78)
    print(f"Image: {IMAGE}")
    print(f"Dimensions: {dimensions[0]} x {dimensions[1]}")
    print(f"Source packets: {len(source)}")
    print(f"Packet size: {len(source[0])} bytes")
    print(f"Padding: {padding} bytes")
    print(f"Seed: {SEED}")
    print(f"Target loss: {LOSS_RATE * 100:.0f}%")

    methods = [
        ("No ECC", lambda channel: run_method(source, channel, "No ECC")),
    ]

    for parity in (2, 4, 8):
        for interleaved in (False, True):
            name = (
                f"RS Interleaved (8+{parity})"
                if interleaved
                else f"RS (8+{parity})"
            )

            methods.append((
                name,
                lambda channel, name=name, parity=parity: run_method(
                    source,
                    channel,
                    name,
                    parity_count=parity,
                ),
            ))

    for overhead in (1.25, 1.50, 2.00):
        methods.append((
            f"Fountain ({overhead:.2f}x)",
            lambda channel, overhead=overhead: run_fountain(
                source,
                channel,
                overhead,
            ),
        ))

    assert len(methods) == 10

    for channel in ("iid", "burst"):
        print(f"\n{channel.upper()} CHANNEL")
        print("-" * 78)
        print(
            f"{'Method':25} {'Tx':>5} {'Loss %':>9} "
            f"{'Exact':>9} {'Recovery %':>12}"
        )
        print("-" * 78)

        for _, execute in methods:
            result = execute(channel)

            assert 0 <= result["exact"] <= len(source)
            assert result["transmitted"] >= len(source)

            print(
                f"{result['method']:25} "
                f"{result['transmitted']:5} "
                f"{result['actual_loss']:9.2f} "
                f"{result['exact']:5}/{len(source):<3} "
                f"{result['recovery']:11.2f}%"
            )

    print("\nUnified satellite demonstration: PASS")


if __name__ == "__main__":
    main()
