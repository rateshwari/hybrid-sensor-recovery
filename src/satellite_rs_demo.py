"""Deterministic satellite-image recovery demonstration."""

from pathlib import Path

from src.satellite_pipeline import (
    load_satellite_image,
    packetize_image,
    reconstruct_image,
    count_exact_packets,
)
from src.recovery import rs_encode_group, rs_decode_group


def main():
    image_path = Path("data/satellite/raw/satellite_000.png")
    output_dir = Path("results/satellite")
    output_dir.mkdir(parents=True, exist_ok=True)

    dimensions, raw = load_satellite_image(image_path)
    packets, padding = packetize_image(raw)

    assert len(packets) == 48

    data_count = 8
    parity_count = 4

    # Erase exactly two source packets in every group.
    # This deterministic pattern is for validation only.
    erased_positions = (1, 5)

    damaged_packets = []
    recovered_packets = []

    for start in range(0, len(packets), data_count):
        group = packets[start:start + data_count]

        encoded = rs_encode_group(group, parity_count)

        # All parity packets are received in this validation test.
        received = encoded.copy()

        for position in erased_positions:
            received[position] = None

        damaged_packets.extend(received[:data_count])

        result = rs_decode_group(
            received,
            data_count=data_count,
            parity_count=parity_count,
        )

        recovered_packets.extend(result.recovered)

    no_ecc_exact = count_exact_packets(
        packets, damaged_packets
    )
    rs_exact = count_exact_packets(
        packets, recovered_packets
    )

    original_image = reconstruct_image(
        packets, dimensions, padding
    )
    damaged_image = reconstruct_image(
        damaged_packets, dimensions, padding
    )
    recovered_image = reconstruct_image(
        recovered_packets, dimensions, padding
    )

    original_image.save(output_dir / "original.png")
    damaged_image.save(output_dir / "no_ecc.png")
    recovered_image.save(output_dir / "rs_recovered.png")

    assert recovered_image.tobytes() == raw
    assert rs_exact == len(packets)

    print(f"Source packets: {len(packets)}")
    print(f"Erased source packets: {len(packets) - no_ecc_exact}")
    print(f"No ECC exact recovery: {no_ecc_exact}/{len(packets)}")
    print(f"RS (8+4) exact recovery: {rs_exact}/{len(packets)}")
    print("Reconstructed image byte-identical: PASS")
    print(f"Images saved in: {output_dir}")


if __name__ == "__main__":
    main()
