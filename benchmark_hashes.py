#!/usr/bin/env python3
"""Benchmark hash algorithms available in Python's hashlib."""

import hashlib
import time
import os
import platform

def benchmark_algorithm(algo: str, data: bytes) -> tuple[float, float]:
    """Benchmark a single algorithm, return (elapsed_seconds, mb_per_second)."""
    h = hashlib.new(algo)
    start = time.perf_counter()
    h.update(data)
    h.hexdigest()
    elapsed = time.perf_counter() - start
    size_mb = len(data) / (1024 * 1024)
    return elapsed, size_mb / elapsed

def main():
    size_mb = 100
    data = os.urandom(size_mb * 1024 * 1024)

    algorithms = [
        'md5',
        'sha1',
        'sha256',
        'sha512',
        'sha3_256',
        'blake2b',
        'blake2s',
    ]

    print(f"System: {platform.system()} {platform.machine()}")
    print(f"Python: {platform.python_version()}")
    print(f"Data size: {size_mb}MB\n")

    print(f"{'Algorithm':<12} {'Time (s)':<10} {'Speed (MB/s)':<12}")
    print("-" * 36)

    results = []
    for algo in algorithms:
        try:
            elapsed, speed = benchmark_algorithm(algo, data)
            results.append((algo, elapsed, speed))
            print(f"{algo:<12} {elapsed:<10.3f} {speed:<12.1f}")
        except Exception as e:
            print(f"{algo:<12} ERROR: {e}")

    # Show ranking
    print("\nRanked by speed:")
    for i, (algo, _, speed) in enumerate(sorted(results, key=lambda x: -x[2]), 1):
        print(f"  {i}. {algo}: {speed:.1f} MB/s")

if __name__ == "__main__":
    main()
