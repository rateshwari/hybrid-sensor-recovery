from src.fountain import FountainSymbol, decode, encode


def make_source(count=6, size=16):
    return [
        bytes((i * 31 + j * 7) % 256 for j in range(size))
        for i in range(count)
    ]


def test_fountain_encoding_is_reproducible():
    source = make_source()

    first = encode(source, output_count=30, seed=7)
    second = encode(source, output_count=30, seed=7)

    assert first == second


def test_decoder_recovers_from_actual_encoded_symbols():
    source = make_source(count=6)

    # Generate redundant encoded symbols using the real encoder.
    symbols = encode(source, output_count=100, seed=7)
    recovered = decode(symbols, source_count=len(source))

    assert recovered == source


def test_decoder_reports_unrecovered_source_packets():
    # No received symbols means no source packets can be recovered.
    recovered = decode([], source_count=3)

    assert recovered == [None, None, None]


def test_decoder_recovers_singleton_symbols():
    source = make_source(count=6)

    symbols = [
        FountainSymbol((i,), packet)
        for i, packet in enumerate(source)
    ]

    assert decode(symbols, source_count=len(source)) == source


def test_decoder_leaves_unrecoverable_packet_missing():
    source = [b"A" * 8, b"B" * 8, b"C" * 8]

    # This equation only connects packets 0 and 1.
    symbols = [FountainSymbol((0, 1), b"A" * 8)]
    recovered = decode(symbols, source_count=3)

    assert recovered[2] is None


def test_fountain_decoder_solves_coupled_equations():
    from src.fountain import FountainSymbol, decode

    a = b"\x11\x22"
    b = b"\x33\x44"
    c = b"\x55\x66"

    def xor(left, right):
        return bytes(x ^ y for x, y in zip(left, right))

    symbols = [
        FountainSymbol((0, 1), xor(a, b)),
        FountainSymbol((1, 2), xor(b, c)),
        FountainSymbol((0, 1, 2), xor(xor(a, b), c)),
    ]

    assert decode(symbols, source_count=3) == [a, b, c]
