import numpy as np
import pandas as pd
import pytest

from src.data_pipeline import (
    dequantize,
    deserialize,
    packetize,
    depacketize,
    quantize,
    serialize,
)


def test_quantize_serialize_packetize_round_trip():
    original = pd.DataFrame({
        "temperature": [20.0, 22.5, 30.0],
        "humidity": [35.0, 50.0, 75.0],
    })

    quantized = quantize(original)
    byte_stream = serialize(quantized)
    packets = packetize(byte_stream, payload_size=8)
    reconstructed_bytes = depacketize(packets)
    reconstructed = deserialize(reconstructed_bytes)

    np.testing.assert_array_equal(reconstructed, quantized)


def test_crc_detects_payload_corruption():
    packets = packetize(b"abcdefgh", payload_size=4)
    damaged = type(packets[0])(
        sequence=packets[0].sequence,
        payload=b"X" + packets[0].payload[1:],
        crc32=packets[0].crc32,
    )

    assert not damaged.valid

    with pytest.raises(ValueError, match="CRC failure"):
        depacketize([damaged, packets[1]])


def test_dequantization_error_is_bounded():
    original = pd.DataFrame({
        "temperature": [20.0, 22.5, 30.0],
        "humidity": [35.0, 50.0, 75.0],
    })

    restored = dequantize(quantize(original))

    assert np.max(np.abs(restored["temperature"] - original["temperature"])) <= (
        125.0 / 65535.0
    )
    assert np.max(np.abs(restored["humidity"] - original["humidity"])) <= (
        100.0 / 65535.0
    )
