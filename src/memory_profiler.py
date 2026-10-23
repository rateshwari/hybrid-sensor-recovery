"""Utilities for measuring Python-tracked memory allocations."""

import gc
import tracemalloc


def measure_peak_memory(operation):
    """
    Execute an operation and measure peak Python-tracked memory.

    Inputs should be prepared before calling this function.

    Returns:
        result: Operation's return value.
        peak_bytes: Peak tracked memory allocation in bytes.
    """

    gc.collect()

    tracemalloc.start()

    try:
        result = operation()
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return result, peak_bytes
