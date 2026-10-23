
"""Burst-loss comparison: No ECC, Reed-Solomon, and Fountain."""

from pathlib import Path
import math
import random
import time

import pandas as pd

from data_pipeline import quantize, serialize
from recovery import no_ecc, rs_encode_group, rs_decode_group
from fountain import encode as fountain_encode, decode as fountain_decode
from experiment import make_fixed_packets, make_groups

DATA_PATH = Path("data/processed/experiment_segment.csv")
RESULT_PATH = Path("results/tables/burst_recovery_results.csv")

PACKET_SIZE = 256
DATA_PER_GROUP = 8
PARITY_PER_GROUP = 2
FOUNTAIN_BLOCK_SIZE = 32
FOUNTAIN_OVERHEADS = [1.5, 2.0]
TRIALS = 30

GOOD_TO_BAD = 0.03
BAD_TO_GOOD = 0.25


def burst_erase_packets(packets, seed: int):
    """Apply a reproducible Gilbert-Elliott packet-erasure channel."""
    rng = random.Random(seed)
    bad_state = False
    received = []

    for packet in packets:
        if bad_state:
            received.append(None)
            if rng.random() < BAD_TO_GOOD:
                bad_state = False
        else:
            received.append(packet)
            if rng.random() < GOOD_TO_BAD:
                bad_state = True

    return received


def run_trial(seed: int) -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    source_bytes = serialize(quantize(df))
    source_packets, _ = make_fixed_packets(source_bytes, PACKET_SIZE)
    groups = make_groups(source_packets)

    rows = []

    # No ECC baseline.
    no_ecc_received = burst_erase_packets(source_packets, seed)
    baseline = no_ecc(no_ecc_received)
    baseline_recovered = sum(
        packet is not None for packet in baseline.recovered
    )
    source_loss_rate = sum(
        packet is None for packet in no_ecc_received
    ) / len(source_packets)

    rows.append({
        "method": "No ECC",
        "seed": seed,
        "source_loss_rate": source_loss_rate,
        "transmission_loss_rate": source_loss_rate,
        "source_packets": len(source_packets),
        "transmitted_packets": len(source_packets),
        "recovered_source_packets": baseline_recovered,
        "source_packet_recovery_rate": (
            baseline_recovered / len(source_packets)
        ),
        "full_source_recovery": (
            baseline_recovered == len(source_packets)
        ),
    })

    # Reed-Solomon (8+2). Preserve the original data-first transmission
    # order so the source stream sees the same loss pattern as No ECC.
    parity_groups = [
        rs_encode_group(group, PARITY_PER_GROUP)[DATA_PER_GROUP:]
        for group in groups
    ]
    parity_stream = [
        packet for parity_group in parity_groups for packet in parity_group
    ]
    rs_stream = source_packets + parity_stream
    rs_received = burst_erase_packets(rs_stream, seed)

    assert rs_received[:len(source_packets)] == no_ecc_received

    exact_rs = 0
    all_rs = True

    for group_index, group in enumerate(groups):
        data_offset = group_index * DATA_PER_GROUP
        data_received = rs_received[
            data_offset:data_offset + DATA_PER_GROUP
        ]

        parity_offset = len(source_packets) + (
            group_index * PARITY_PER_GROUP
        )
        parity_received = rs_received[
            parity_offset:parity_offset + PARITY_PER_GROUP
        ]

        result = rs_decode_group(
            data_received + parity_received,
            data_count=DATA_PER_GROUP,
            parity_count=PARITY_PER_GROUP,
        )

        real_count = min(
            DATA_PER_GROUP, len(source_packets) - data_offset
        )

        for i in range(real_count):
            if result.recovered[i] == group[i]:
                exact_rs += 1
            else:
                all_rs = False

    rows.append({
        "method": "Reed-Solomon (8+2)",
        "seed": seed,
        "source_loss_rate": source_loss_rate,
        "transmission_loss_rate": (
            sum(packet is None for packet in rs_received)
            / len(rs_received)
        ),
        "source_packets": len(source_packets),
        "transmitted_packets": len(rs_stream),
        "recovered_source_packets": exact_rs,
        "source_packet_recovery_rate": exact_rs / len(source_packets),
        "full_source_recovery": all_rs,
    })

    # Fountain symbols pass through the same Gilbert-Elliott channel model.
    # The random stream is independent for each method/block because coded
    # symbols differ in count and meaning from source packets.
    for overhead in FOUNTAIN_OVERHEADS:
        exact = 0
        all_recovered = True
        total_symbols = 0
        total_lost_symbols = 0
        encoding_seconds = 0.0
        decoding_seconds = 0.0

        for block_index, offset in enumerate(
            range(0, len(source_packets), FOUNTAIN_BLOCK_SIZE)
        ):
            block = source_packets[
                offset:offset + FOUNTAIN_BLOCK_SIZE
            ]
            count = len(block)
            output_count = max(count, math.ceil(count * overhead))

            start = time.perf_counter()
            symbols = fountain_encode(
                block,
                output_count=output_count,
                seed=seed + block_index * 1009,
            )
            encoding_seconds += time.perf_counter() - start
            total_symbols += len(symbols)

            received_symbols = burst_erase_packets(
                symbols,
                seed + 500_009 + block_index,
            )
            total_lost_symbols += sum(
                symbol is None for symbol in received_symbols
            )
            received_symbols = [
                symbol for symbol in received_symbols if symbol is not None
            ]

            start = time.perf_counter()
            recovered = fountain_decode(
                received_symbols, source_count=count
            )
            decoding_seconds += time.perf_counter() - start

            for i in range(count):
                if recovered[i] == block[i]:
                    exact += 1
                else:
                    all_recovered = False

        rows.append({
            "method": f"Fountain ({overhead:.1f}x)",
            "seed": seed,
            # Source packets are not transmitted directly in Fountain;
            # use NaN rather than mislabeling symbol loss as source loss.
            "source_loss_rate": float("nan"),
            "transmission_loss_rate": (
                total_lost_symbols / total_symbols
            ),
            "source_packets": len(source_packets),
            "transmitted_packets": total_symbols,
            "recovered_source_packets": exact,
            "source_packet_recovery_rate": exact / len(source_packets),
            "full_source_recovery": all_recovered,
            "encoding_seconds": encoding_seconds,
            "decoding_seconds": decoding_seconds,
        })

    return rows


def main():
    all_rows = []

    for trial in range(TRIALS):
        all_rows.extend(run_trial(seed=42 + trial))

    results = pd.DataFrame(all_rows)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULT_PATH, index=False)

    summary = (
        results.groupby("method")
        .agg(
            mean_source_loss=("source_loss_rate", "mean"),
            mean_transmission_loss=("transmission_loss_rate", "mean"),
            mean_packet_recovery=("source_packet_recovery_rate", "mean"),
            full_recovery_fraction=("full_source_recovery", "mean"),
            mean_transmitted_packets=("transmitted_packets", "mean"),
        )
        .reset_index()
    )

    print("=== PAIRED BURST-LOSS SUMMARY ===")
    print(summary.to_string(index=False))
    print(f"\nDetailed results saved to: {RESULT_PATH}")


if __name__ == "__main__":
    main()
