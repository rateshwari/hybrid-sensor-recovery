"""Packet-level trace for the validated burst-erasure experiment."""

from functools import lru_cache

import pandas as pd

from src.burst_experiment import (
    DATA_PATH,
    DATA_PER_GROUP,
    PACKET_SIZE,
    burst_erase_packets,
    deinterleave_rs_packets,
    interleave_rs_groups,
)
from src.data_pipeline import quantize, serialize
from src.experiment import make_fixed_packets, make_groups
from src.recovery import rs_decode_group, rs_encode_group


@lru_cache(maxsize=1)
def load_source_packets():
    df = pd.read_csv(DATA_PATH)
    source_bytes = serialize(quantize(df))
    packets, _ = make_fixed_packets(source_bytes, PACKET_SIZE)
    return tuple(packets)


def packet_trace(seed: int, loss_rate: float, parity_count: int, interleaved: bool):
    if not 0 < loss_rate <= 0.75:
        raise ValueError("loss_rate must be greater than 0 and at most 0.75.")

    if parity_count not in (2, 4, 8):
        raise ValueError("parity_count must be 2, 4, or 8.")

    source_packets = list(load_source_packets())
    groups = make_groups(source_packets)

    encoded_groups = [
        rs_encode_group(group, parity_count)
        for group in groups
    ]

    if interleaved:
        transmitted, positions = interleave_rs_groups(encoded_groups)
    else:
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

    if interleaved:
        restored_groups = deinterleave_rs_packets(
            received,
            positions,
            group_count=len(encoded_groups),
            group_length=DATA_PER_GROUP + parity_count,
        )
    else:
        restored_groups = []
        for group_index in range(len(groups)):
            source_offset = group_index * DATA_PER_GROUP
            parity_offset = len(source_packets) + group_index * parity_count

            restored_groups.append(
                received[source_offset:source_offset + DATA_PER_GROUP]
                + received[parity_offset:parity_offset + parity_count]
            )

    statuses = []

    for group_index, original_group in enumerate(groups):
        received_group = restored_groups[group_index]

        result = rs_decode_group(
            received_group,
            data_count=DATA_PER_GROUP,
            parity_count=parity_count,
        )

        for packet_index, original_packet in enumerate(original_group):
            received_packet = received_group[packet_index]
            recovered_packet = result.recovered[packet_index]

            if received_packet == original_packet:
                status = "received"
            elif recovered_packet == original_packet:
                status = "recovered"
            else:
                status = "unrecovered"

            statuses.append(status)

    return {
        "method": (
            f"Reed-Solomon Interleaved (8+{parity_count})"
            if interleaved
            else f"Reed-Solomon (8+{parity_count})"
        ),
        "seed": seed,
        "target_loss_rate": loss_rate,
        "source_packets": len(source_packets),
        "transmitted_packets": len(transmitted),
        "received_count": statuses.count("received"),
        "recovered_count": statuses.count("recovered"),
        "unrecovered_count": statuses.count("unrecovered"),
        "packet_statuses": statuses,
    }
