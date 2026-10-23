"""LT-style Fountain coding with a Robust Soliton degree distribution."""

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class FountainSymbol:
    indices: tuple[int, ...]
    payload: bytes


def xor_bytes(chunks: list[bytes]) -> bytes:
    if not chunks:
        raise ValueError("At least one chunk is required.")

    result = bytearray(chunks[0])

    for chunk in chunks[1:]:
        if len(chunk) != len(result):
            raise ValueError("All chunks must have equal length.")

        for i, value in enumerate(chunk):
            result[i] ^= value

    return bytes(result)


def robust_soliton_distribution(
    source_count: int,
    c: float = 0.1,
    delta: float = 0.05,
) -> list[float]:
    """Return Robust Soliton probabilities for degrees 1..source_count."""
    if source_count < 1:
        raise ValueError("source_count must be positive.")
    if c <= 0:
        raise ValueError("c must be positive.")
    if not 0 < delta < 1:
        raise ValueError("delta must be between 0 and 1.")

    k = source_count
    r = c * math.log(k / delta) * math.sqrt(k)
    pivot = max(1, min(k, int(k / r)))

    rho = [0.0] * (k + 1)
    rho[1] = 1.0 / k

    for degree in range(2, k + 1):
        rho[degree] = 1.0 / (degree * (degree - 1))

    tau = [0.0] * (k + 1)

    for degree in range(1, min(pivot, k)):
        tau[degree] = r / (degree * k)

    tau[pivot] = r * math.log(r / delta) / k

    probabilities = [
        rho[degree] + tau[degree]
        for degree in range(1, k + 1)
    ]

    total = sum(probabilities)
    return [p / total for p in probabilities]


def encode(
    source_packets: list[bytes],
    output_count: int,
    seed: int = 42,
) -> list[FountainSymbol]:
    """Generate reproducible XOR combinations of source packets."""
    if not source_packets:
        raise ValueError("Source packets cannot be empty.")
    if output_count < len(source_packets):
        raise ValueError("Output count must be at least source count.")

    size = len(source_packets[0])

    if size == 0 or any(len(p) != size for p in source_packets):
        raise ValueError("Source packets must have equal nonzero size.")

    probabilities = robust_soliton_distribution(len(source_packets))
    rng = random.Random(seed)
    symbols = []

    degrees = list(range(1, len(source_packets) + 1))

    for _ in range(output_count):
        degree = rng.choices(degrees, weights=probabilities, k=1)[0]
        indices = tuple(sorted(rng.sample(range(len(source_packets)), degree)))
        payload = xor_bytes([source_packets[i] for i in indices])
        symbols.append(FountainSymbol(indices, payload))

    return symbols




def decode(
    received_symbols: list[FountainSymbol],
    source_count: int,
) -> list[bytes | None]:
    """Decode XOR symbols using Gaussian elimination over GF(2)."""
    if source_count < 1:
        raise ValueError("source_count must be positive.")

    equations = []

    for symbol in received_symbols:
        if not symbol.indices:
            continue

        if len(set(symbol.indices)) != len(symbol.indices):
            raise ValueError("A symbol contains duplicate source indices.")

        if any(i < 0 or i >= source_count for i in symbol.indices):
            raise ValueError("A symbol contains an invalid source index.")

        if not symbol.payload:
            raise ValueError("Symbol payloads must not be empty.")

        equations.append((set(symbol.indices), bytes(symbol.payload)))

    if not equations:
        return [None] * source_count

    payload_size = len(equations[0][1])

    if any(len(payload) != payload_size for _, payload in equations):
        raise ValueError("All symbol payloads must have equal nonzero size.")

    # Represent each XOR equation as a bit mask and a byte-vector RHS.
    rows = []

    for indices, payload in equations:
        mask = 0
        for index in indices:
            mask |= 1 << index

        rows.append([mask, bytearray(payload)])

    # Reduced row-echelon elimination over GF(2).
    pivot_row = 0

    for column in range(source_count):
        bit = 1 << column

        candidate = next(
            (
                row_index
                for row_index in range(pivot_row, len(rows))
                if rows[row_index][0] & bit
            ),
            None,
        )

        if candidate is None:
            continue

        rows[pivot_row], rows[candidate] = rows[candidate], rows[pivot_row]
        pivot_mask, pivot_rhs = rows[pivot_row]

        # Eliminate this variable from every other equation.
        for row_index in range(len(rows)):
            if row_index == pivot_row:
                continue

            mask, rhs = rows[row_index]

            if mask & bit:
                rows[row_index][0] = mask ^ pivot_mask

                for j in range(payload_size):
                    rhs[j] ^= pivot_rhs[j]

        pivot_row += 1

        if pivot_row == len(rows):
            break

    recovered: dict[int, bytes] = {}

    for mask, rhs in rows:
        if mask == 0:
            if any(rhs):
                raise ValueError("Inconsistent Fountain equations.")
            continue

        # A singleton equation uniquely identifies its source packet.
        if mask & (mask - 1) == 0:
            index = mask.bit_length() - 1
            recovered[index] = bytes(rhs)

    return [recovered.get(i) for i in range(source_count)]
