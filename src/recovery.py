"""Baseline and packet-level Reed-Solomon recovery."""

from dataclasses import dataclass

from reedsolo import RSCodec
from threading import RLock

_rs_thread_lock = RLock()


@dataclass
class RecoveryResult:
    recovered: list[bytes | None]
    success: bool
    recovered_count: int
    reason: str


def no_ecc(
    data_packets: list[bytes | None],
) -> RecoveryResult:
    """Return packets as received; do not repair missing data."""
    missing = sum(packet is None for packet in data_packets)

    return RecoveryResult(
        recovered=list(data_packets),
        success=(missing == 0),
        recovered_count=0,
        reason="No ECC: missing packets remain unrecovered.",
    )


def _rs_encode_group_impl(
    data_packets: list[bytes],
    parity_count: int = 2,
) -> list[bytes]:
    """Return data packets followed by RS parity packets.

    Each byte position is coded independently across the packet group.
    All input packets must have the same length.
    """
    if not data_packets:
        raise ValueError("At least one data packet is required.")

    if parity_count < 1:
        raise ValueError("parity_count must be at least 1.")

    packet_size = len(data_packets[0])

    if packet_size == 0:
        raise ValueError("Packets must not be empty.")

    if any(len(packet) != packet_size for packet in data_packets):
        raise ValueError("All data packets must have the same length.")

    k = len(data_packets)
    if k + parity_count > 255:
        raise ValueError("Data plus parity packets must not exceed 255.")

    codec = RSCodec(nsym=parity_count, nsize=k + parity_count)
    parity_packets = [bytearray(packet_size) for _ in range(parity_count)]

    for byte_index in range(packet_size):
        symbols = bytes(packet[byte_index] for packet in data_packets)
        codeword = codec.encode(symbols)

        for p in range(parity_count):
            parity_packets[p][byte_index] = codeword[k + p]

    return list(data_packets) + [bytes(packet) for packet in parity_packets]


def _rs_decode_group_impl(
    received_packets: list[bytes | None],
    data_count: int,
    parity_count: int = 2,
) -> RecoveryResult:
    """Recover missing packets when erasures are within RS capacity.

    The list must contain data packets first, followed by parity packets.
    None represents a packet known to be erased or rejected by CRC.
    """
    total = data_count + parity_count

    if data_count < 1 or parity_count < 1:
        raise ValueError("Data and parity counts must both be positive.")

    if total > 255:
        raise ValueError("Data plus parity packets must not exceed 255.")

    if len(received_packets) != total:
        raise ValueError(f"Expected {total} received packet slots.")

    present = [p for p in received_packets if p is not None]
    if not present:
        return RecoveryResult(
            [None] * data_count, False, 0, "No packets received."
        )

    packet_size = len(present[0])
    if any(len(p) != packet_size for p in present):
        raise ValueError("All received packets must have the same length.")

    erased_positions = [
        i for i, packet in enumerate(received_packets) if packet is None
    ]

    if len(erased_positions) > parity_count:
        return RecoveryResult(
            list(received_packets[:data_count]),
            False,
            0,
            "Erasure count exceeds configured parity capacity.",
        )

    codec = RSCodec(nsym=parity_count, nsize=total)
    recovered = [bytearray(packet_size) for _ in range(data_count)]

    try:
        for byte_index in range(packet_size):
            codeword = bytearray(
                packet[byte_index] if packet is not None else 0
                for packet in received_packets
            )

            decoded, full_codeword, _ = codec.decode(
                codeword,
                erase_pos=erased_positions,
            )

            # Confirm that decoded data matches the original data positions.
            for data_index in range(data_count):
                recovered[data_index][byte_index] = decoded[data_index]

    except Exception as exc:
        return RecoveryResult(
            list(received_packets[:data_count]),
            False,
            0,
            f"RS decoding failed: {exc}",
        )

    recovered_bytes = [bytes(packet) for packet in recovered]
    recovered_count = sum(
        received_packets[i] is None for i in range(data_count)
    )

    return RecoveryResult(
        recovered=recovered_bytes,
        success=True,
        recovered_count=recovered_count,
        reason="RS decoding completed.",
    )


def rs_encode_group(
    data_packets: list[bytes],
    parity_count: int = 2,
) -> list[bytes]:
    """Thread-safe Reed-Solomon packet encoding."""
    with _rs_thread_lock:
        return _rs_encode_group_impl(data_packets, parity_count)


def rs_decode_group(
    received_packets: list[bytes | None],
    data_count: int,
    parity_count: int = 2,
) -> RecoveryResult:
    """Thread-safe Reed-Solomon packet decoding."""
    with _rs_thread_lock:
        return _rs_decode_group_impl(
            received_packets, data_count, parity_count
        )
