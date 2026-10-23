"""Memory profiling experiments for error-correction algorithms."""

from pathlib import Path

import pandas as pd

from data_pipeline import quantize, serialize
from experiment import make_fixed_packets, make_groups
from recovery import rs_encode_group
from memory_profiler import measure_peak_memory
from fountain import encode as fountain_encode
from burst_experiment import FOUNTAIN_BLOCK_SIZE
from recovery import rs_decode_group
from burst_experiment import burst_erase_packets
from fountain import decode as fountain_decode
from burst_experiment import burst_erase_packets
from burst_experiment import (
    interleave_rs_groups,
    deinterleave_rs_packets,
)
from recovery import no_ecc


DATA_PATH = Path("data/processed/experiment_segment.csv")
PACKET_SIZE = 256
DATA_PER_GROUP = 8
PARITY_OPTIONS = [2, 4, 8]


def load_source_packets():
    """Load the same dataset used in recovery experiments."""

    df = pd.read_csv(DATA_PATH)

    source_bytes = serialize(quantize(df))

    source_packets, _ = make_fixed_packets(
        source_bytes,
        PACKET_SIZE,
    )

    return source_packets


def measure_rs_encoding(source_packets, parity_count):
    """Measure RS encoding peak Python-tracked memory."""

    groups = make_groups(source_packets)

    def encode_operation():
        return [
            rs_encode_group(group, parity_count)
            for group in groups
        ]

    encoded_groups, peak_bytes = measure_peak_memory(
        encode_operation
    )

    return {
        "method": f"Reed-Solomon (8+{parity_count})",
        "source_packets": len(source_packets),
        "encoded_groups": len(encoded_groups),
        "transmitted_packets": sum(
            len(group) for group in encoded_groups
        ),
        "encoding_peak_memory_kib": peak_bytes / 1024,
    }

def measure_fountain_encoding(source_packets, overhead, seed=42):
    """Measure Fountain encoding peak Python-tracked memory."""

    import math

    blocks = [
        source_packets[i:i + FOUNTAIN_BLOCK_SIZE]
        for i in range(0, len(source_packets), FOUNTAIN_BLOCK_SIZE)
    ]

    def encode_operation():
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

        return encoded_blocks

    encoded_blocks, peak_bytes = measure_peak_memory(
        encode_operation
    )

    return {
        "method": f"Fountain ({overhead:.2f}x)",
        "source_packets": len(source_packets),
        "encoded_groups": len(encoded_blocks),
        "transmitted_packets": sum(
            len(block) for block in encoded_blocks
        ),
        "encoding_peak_memory_kib": peak_bytes / 1024,
    }

def measure_rs_decoding(
    source_packets, parity_count, seed=42, loss_rate=0.25
):
    """Measure RS decoding memory under burst packet loss."""

    groups = make_groups(source_packets)

    encoded_groups = [
        rs_encode_group(group, parity_count)
        for group in groups
    ]

    parity_stream = [
        packet
        for encoded in encoded_groups
        for packet in encoded[DATA_PER_GROUP:]
    ]

    transmitted = source_packets + parity_stream

    received = burst_erase_packets(
        transmitted,
        seed=seed,
        loss_rate=loss_rate,
    )

    received_groups = []

    for group_index in range(len(groups)):
        data_start = group_index * DATA_PER_GROUP
        parity_start = (
            len(source_packets)
            + group_index * parity_count
        )

        received_groups.append(
            received[data_start:data_start + DATA_PER_GROUP]
            + received[parity_start:parity_start + parity_count]
        )

    def decode_operation():
        return [
            rs_decode_group(
                group,
                data_count=DATA_PER_GROUP,
                parity_count=parity_count,
            )
            for group in received_groups
        ]

    decoded_groups, peak_bytes = measure_peak_memory(
        decode_operation
    )

    recovered_count = sum(
        decoded.recovered[i] == original[i]
        for decoded, original in zip(decoded_groups, groups)
        for i in range(DATA_PER_GROUP)
    )

    return {
        "method": f"Reed-Solomon (8+{parity_count})",
        "decoding_peak_memory_kib": peak_bytes / 1024,
        "recovered_packets": recovered_count,
        "recovery_rate": recovered_count / len(source_packets),
    }

def measure_fountain_decoding(
    source_packets, overhead, seed=42, loss_rate=0.25
):
    """Measure Fountain decoding memory under burst packet loss."""

    import math

    blocks = [
        source_packets[i:i + FOUNTAIN_BLOCK_SIZE]
        for i in range(0, len(source_packets), FOUNTAIN_BLOCK_SIZE)
    ]

    encoded_blocks = []

    for block_index, block in enumerate(blocks):
        symbols = fountain_encode(
            block,
            output_count=max(
                len(block),
                math.ceil(len(block) * overhead),
            ),
            seed=seed + block_index * 1009,
        )

        encoded_blocks.append(symbols)

    transmitted = [
        symbol
        for block in encoded_blocks
        for symbol in block
    ]

    received = burst_erase_packets(
        transmitted,
        seed=seed + 500_009,
        loss_rate=loss_rate,
    )

    received_blocks = []
    offset = 0

    for encoded_block in encoded_blocks:
        block_length = len(encoded_block)

        received_blocks.append([
            symbol
            for symbol in received[offset:offset + block_length]
            if symbol is not None
        ])

        offset += block_length

    def decode_operation():
        return [
            fountain_decode(
                symbols,
                source_count=len(original),
            )
            for symbols, original in zip(received_blocks, blocks)
        ]

    decoded_blocks, peak_bytes = measure_peak_memory(
        decode_operation
    )

    recovered_count = sum(
        recovered == original
        for decoded, block in zip(decoded_blocks, blocks)
        for recovered, original in zip(decoded, block)
    )

    return {
        "method": f"Fountain ({overhead:.2f}x)",
        "decoding_peak_memory_kib": peak_bytes / 1024,
        "recovered_packets": recovered_count,
        "recovery_rate": recovered_count / len(source_packets),
    }

def measure_interleaved_rs(
    source_packets, parity_count, seed=42, loss_rate=0.25
):
    """Profile complete interleaved RS encoding and decoding."""

    groups = make_groups(source_packets)

    def encode_operation():
        encoded_groups = [
            rs_encode_group(group, parity_count)
            for group in groups
        ]

        return interleave_rs_groups(encoded_groups)

    (transmitted, positions), encoding_peak = (
        measure_peak_memory(encode_operation)
    )

    received = burst_erase_packets(
        transmitted,
        seed=seed,
        loss_rate=loss_rate,
    )

    def decode_operation():
        restored_groups = deinterleave_rs_packets(
            received,
            positions,
            group_count=len(groups),
            group_length=DATA_PER_GROUP + parity_count,
        )

        return [
            rs_decode_group(
                group,
                data_count=DATA_PER_GROUP,
                parity_count=parity_count,
            )
            for group in restored_groups
        ]

    decoded_groups, decoding_peak = (
        measure_peak_memory(decode_operation)
    )

    recovered_count = sum(
        decoded.recovered[i] == original[i]
        for decoded, original in zip(decoded_groups, groups)
        for i in range(len(original))
    )

    return {
        "method": f"RS Interleaved (8+{parity_count})",
        "source_packets": len(source_packets),
        "encoded_groups": len(groups),
        "transmitted_packets": len(transmitted),
        "encoding_peak_memory_kib": encoding_peak / 1024,
        "decoding_peak_memory_kib": decoding_peak / 1024,
        "recovered_packets": recovered_count,
        "recovery_rate": recovered_count / len(source_packets),
    }

def measure_no_ecc_memory(
    source_packets, seed=42, loss_rate=0.25
):
    """Profile the No ECC baseline under burst packet loss."""

    def encode_operation():
        return list(source_packets)

    transmitted, encoding_peak = measure_peak_memory(
        encode_operation
    )

    received = burst_erase_packets(
        transmitted,
        seed=seed,
        loss_rate=loss_rate,
    )

    def decode_operation():
        return no_ecc(received)

    decoded, decoding_peak = measure_peak_memory(
        decode_operation
    )

    recovered_count = sum(
        recovered == original
        for recovered, original in zip(
            decoded.recovered,
            source_packets,
        )
    )

    return {
        "method": "No ECC",
        "source_packets": len(source_packets),
        "encoded_groups": 0,
        "transmitted_packets": len(transmitted),
        "encoding_peak_memory_kib": encoding_peak / 1024,
        "decoding_peak_memory_kib": decoding_peak / 1024,
        "recovered_packets": recovered_count,
        "recovery_rate": recovered_count / len(source_packets),
    }

def main():
    source_packets = load_source_packets()

    print(f"\nSource packets: {len(source_packets)}")

    results = []
    baseline_result = measure_no_ecc_memory(
        source_packets
    )

    results.append(baseline_result)

    for parity_count in PARITY_OPTIONS:
        result = measure_rs_encoding(
            source_packets,
            parity_count,
        )

        decoding_result = measure_rs_decoding(
            source_packets,
            parity_count,
        )

        result.update({
            "decoding_peak_memory_kib":
                decoding_result["decoding_peak_memory_kib"],
            "recovered_packets":
                decoding_result["recovered_packets"],
            "recovery_rate":
                decoding_result["recovery_rate"],
        })

        results.append(result)

    for parity_count in PARITY_OPTIONS:
        result = measure_interleaved_rs(
            source_packets,
            parity_count,
        )

        results.append(result)

    for overhead in [1.25, 1.5, 2.0]:
        result = measure_fountain_encoding(
            source_packets,
            overhead,
        )

        decoding_result = measure_fountain_decoding(
            source_packets,
            overhead,
        )

        result.update({
            "decoding_peak_memory_kib":
                decoding_result["decoding_peak_memory_kib"],
            "recovered_packets":
                decoding_result["recovered_packets"],
            "recovery_rate":
                decoding_result["recovery_rate"],
        })

        results.append(result)

    summary = pd.DataFrame(results)

    output_path = Path(
        "results/tables/memory_profile_single_trial.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        output_path,
        index=False,
    )

    print(f"\nSaved memory results to: {output_path}")

    print("\n=== RS VS FOUNTAIN ENCODING MEMORY ===")
    print(summary.to_string(index=False))

    assert len(summary) == 10
    assert summary["encoding_peak_memory_kib"].gt(0).all()

    print("\nPASS: All ten coding configurations profiled.")


if __name__ == "__main__":
    main()
