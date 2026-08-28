"""
Research reporting utilities.

This module converts benchmark results into
machine-readable and human-readable reports.

Scope:
    - Local research benchmarks
    - Reproducible experiment records
    - JSON serialization
    - Human-readable summaries

No real cryptographic key material is handled here.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any


def _make_json_safe(value: Any) -> Any:
    """
    Convert common Python objects into JSON-safe values.

    Handles:
        - tuples
        - lists
        - dictionaries
        - primitive values
    """

    if isinstance(value, tuple):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, list):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }

    return value


def benchmark_to_dict(
    benchmark,
) -> dict[str, Any]:
    """
    Convert a BenchmarkRun object into a
    JSON-safe dictionary.
    """

    data = asdict(benchmark)

    return _make_json_safe(data)


def benchmark_to_json(
    benchmark,
    indent: int = 2,
) -> str:
    """
    Serialize a BenchmarkRun into JSON text.
    """

    data = benchmark_to_dict(
        benchmark
    )

    return json.dumps(
        data,
        indent=indent,
        sort_keys=True,
    )


def save_benchmark_json(
    benchmark,
    path: str | Path,
) -> Path:
    """
    Save a benchmark result as JSON.

    Parameters
    ----------
    benchmark:
        BenchmarkRun instance.

    path:
        Output JSON path.

    Returns
    -------
    Path
        Resolved output path.
    """

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        benchmark_to_json(benchmark),
        encoding="utf-8",
    )

    return output_path


def benchmark_summary_text(
    benchmark,
) -> str:
    """
    Generate a human-readable benchmark summary.
    """

    lines = [
        "Quantum Attack Toolkit Benchmark",
        "=" * 40,
        f"Attack:              {benchmark.attack}",
        f"Target:              {benchmark.target}",
        f"Target type:         {benchmark.target_type}",
        f"Size:                {benchmark.size}",
        f"Success:             {benchmark.success}",
        f"Logical qubits:      {benchmark.logical_qubits}",
        f"Circuit depth:       {benchmark.circuit_depth}",
        f"Gate count:          {benchmark.gate_count}",
        f"Shots:               {benchmark.shots}",
        f"Success probability:  {benchmark.success_probability:.4f}",
        f"Elapsed seconds:     {benchmark.elapsed_seconds:.6f}",
        "",
        "Metrics",
        "-" * 40,
    ]

    for key, value in benchmark.metrics.items():
        lines.append(
            f"{key}: {value}"
        )

    lines.extend(
        [
            "",
            "Notes",
            "-" * 40,
        ]
    )

    for note in benchmark.notes:
        lines.append(
            f"- {note}"
        )

    return "\n".join(lines)


def save_benchmark_summary(
    benchmark,
    path: str | Path,
) -> Path:
    """
    Save a human-readable benchmark report.
    """

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        benchmark_summary_text(benchmark),
        encoding="utf-8",
    )

    return output_path