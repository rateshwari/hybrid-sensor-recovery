"""Controlled packet-erasure experiment: No ECC vs Reed-Solomon."""

from pathlib import Path
import random
import time

import pandas as pd

from data_pipeline import quantize, serialize
from recovery import no_ecc, rs_encode_group, rs_decode_group

DATA_PATH = Path("data/processed/experiment_segment.csv")
RESULT_PATH = Path("results/tables/packet_recovery_results.csv")

PACKET_SIZE = 256
DATA_PER_GROUP = 8
PARITY_PER_GROUP = 2
LOSS_RATES = [0.05, 0.10, 0.20, 0.30]
TRIALS = 30


def make_fixed_packets(data: bytes, packet_size: int):
    """Split bytes into fixed-size packets, padding the final packet."""
    original_length = len(data)
    padding = (-original_length) % packet_size
    padded = data + bytes(padding)

    packets = [
        padded[i:i + packet_size]
        for i in range(0, len(padded), packet_size)
    ]
    return packets, original_length


def make_groups(packets: list[bytes]) -> list[list[bytes]]:
    """Create groups of equal-sized data packets."""
    groups = []

    for i in range(0, len(packets), DATA_PER_GROUP):
        group = packets[i:i + DATA_PER_GROUP]

        while len(group) < DATA_PER_GROUP:
            group.append(bytes(PACKET_SIZE))

        groups.append(group)

    return groups


def erase_packets(packets, probability: float, seed: int):
    """Apply reproducible independent packet loss."""
    rng = random.Random(seed)

    return [
        packet if rng.random() >= probability else None
        for packet in packets
    ]


def burst_erase_packets(
    packets,
    good_to_bad: float = 0.03,
    bad_to_good: float = 0.25,
    seed: int = 42,
):
    """Simulate burst packet erasures using a two-state channel.

    GOOD state: packets arrive.
    BAD state: packets are lost.
    """
    rng = random.Random(seed)
    bad_state = False
    received = []

    for packet in packets:
        if bad_state:
            received.append(None)
            if rng.random() < bad_to_good:
                bad_state = False
        else:
            received.append(packet)
            if rng.random() < good_to_bad:
                bad_state = True

    return received



def run_trial(loss_rate: float, seed: int) -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    quantized = quantize(df)
    source_bytes = serialize(quantized)

    source_packets, _ = make_fixed_packets(source_bytes, PACKET_SIZE)
    groups = make_groups(source_packets)

    rows = []

    # No ECC baseline.
    no_ecc_start_time = time.perf_counter()

    no_ecc_received = erase_packets(
        source_packets,
        loss_rate,
        seed,
    )
    no_ecc_result = no_ecc(no_ecc_received)

    no_ecc_elapsed = time.perf_counter() - no_ecc_start_time

    no_ecc_recovered = sum(
        packet is not None
        for packet in no_ecc_result.recovered
    )

    rows.append({
        "method": "No ECC",
        "loss_rate": loss_rate,
        "seed": seed,
        "source_packets": len(source_packets),
        "transmitted_packets": len(source_packets),
        "recovered_source_packets": no_ecc_recovered,
        "source_packet_recovery_rate": (
            no_ecc_recovered / len(source_packets)
        ),
        "full_source_recovery": (
            no_ecc_recovered == len(source_packets)
        ),
        "decode_seconds": no_ecc_elapsed,
    })

    # Reed-Solomon: same source-packet losses as No ECC;
    # parity packets experience their own independent losses.
    rs_start_time = time.perf_counter()

    exact_recovered_packets = 0
    all_source_packets_recovered = True
    transmitted_count = 0

    for group_index, group in enumerate(groups):
        encoded = rs_encode_group(group, PARITY_PER_GROUP)
        transmitted_count += len(encoded)

        group_offset = group_index * DATA_PER_GROUP
        group_end = group_offset + DATA_PER_GROUP

        received_data = no_ecc_received[group_offset:group_end]

        parity_rng = random.Random(
            seed + 1_000_003 + group_index
        )

        received_parity = [
            packet if parity_rng.random() >= loss_rate else None
            for packet in encoded[DATA_PER_GROUP:]
        ]

        received = received_data + received_parity

        result = rs_decode_group(
            received,
            data_count=DATA_PER_GROUP,
            parity_count=PARITY_PER_GROUP,
        )

        real_count = min(
            DATA_PER_GROUP,
            len(source_packets) - group_offset,
        )

        for i in range(real_count):
            # Count a packet only if its reconstructed bytes match exactly.
            # Intact packets still count even if the group exceeds RS capacity.
            if result.recovered[i] == group[i]:
                exact_recovered_packets += 1
            else:
                all_source_packets_recovered = False

    rs_elapsed = time.perf_counter() - rs_start_time

    rows.append({
        "method": "Reed-Solomon (8+2)",
        "loss_rate": loss_rate,
        "seed": seed,
        "source_packets": len(source_packets),
        "transmitted_packets": transmitted_count,
        "recovered_source_packets": exact_recovered_packets,
        "source_packet_recovery_rate": (
            exact_recovered_packets / len(source_packets)
        ),
        "full_source_recovery": all_source_packets_recovered,
        "decode_seconds": rs_elapsed,
    })

    return rows


def main():
    all_rows = []

    for loss_rate in LOSS_RATES:
        for trial in range(TRIALS):
            seed = 42 + trial
            all_rows.extend(run_trial(loss_rate, seed))

    results = pd.DataFrame(all_rows)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULT_PATH, index=False)

    summary = (
        results.groupby(["method", "loss_rate"])
        .agg(
            mean_packet_recovery=(
                "source_packet_recovery_rate", "mean"
            ),
            full_recovery_fraction=("full_source_recovery", "mean"),
            mean_elapsed_seconds=("decode_seconds", "mean"),
            transmitted_packets=("transmitted_packets", "mean"),
        )
        .reset_index()
    )

    print("=== PACKET RECOVERY SUMMARY ===")
    print(summary.to_string(index=False))
    print(f"\nDetailed trials saved to: {RESULT_PATH}")


if __name__ == "__main__":
    main()
