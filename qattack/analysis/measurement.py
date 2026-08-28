"""
Measurement distribution analysis utilities.

This module provides reusable statistical analysis for quantum
measurement-count dictionaries.

The functions are intentionally backend-agnostic so that measurement
results from simulators, IBM Quantum hardware, or other authorized
execution backends can be analyzed using the same interface.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Iterable
from typing import TypeAlias


Counts: TypeAlias = Mapping[str, int]


def _validate_counts(
    counts: Counts,
    *,
    allow_empty: bool = False,
) -> None:
    """
    Validate a measurement-count mapping.

    Parameters
    ----------
    counts:
        Mapping of measurement states to integer counts.

    allow_empty:
        If True, an empty mapping is accepted.

    Raises
    ------
    TypeError
        If counts or its keys/values have invalid types.

    ValueError
        If counts contain negative values or invalid totals.
    """

    if not isinstance(counts, Mapping):
        raise TypeError(
            "counts must be a mapping of bitstrings to integer counts."
        )

    if not counts:
        if allow_empty:
            return

        raise ValueError(
            "counts must not be empty."
        )

    for state, count in counts.items():
        if not isinstance(state, str):
            raise TypeError(
                "measurement states must be strings."
            )

        if not isinstance(count, int):
            raise TypeError(
                "measurement counts must be integers."
            )

        if isinstance(count, bool):
            raise TypeError(
                "measurement counts must be integers, not booleans."
            )

        if count < 0:
            raise ValueError(
                "measurement counts must be non-negative."
            )

    if sum(counts.values()) <= 0:
        raise ValueError(
            "total measurement count must be greater than zero."
        )


def total_shots(
    counts: Counts,
) -> int:
    """
    Return the total number of measurement shots.
    """

    _validate_counts(counts)

    return sum(counts.values())


def measurement_probabilities(
    counts: Counts,
) -> dict[str, float]:
    """
    Convert measurement counts into probabilities.

    Empty distributions return an empty dictionary.

    Example
    -------
    >>> measurement_probabilities({"00": 75, "11": 25})
    {'00': 0.75, '11': 0.25}
    """

    if not counts:
        return {}

    _validate_counts(counts)

    shots = total_shots(counts)

    return {
        state: count / shots
        for state, count in counts.items()
    }


def probability_mass(
    counts: Counts,
    states: Iterable[str] | None = None,
) -> float:
    """
    Calculate probability mass contained in selected states.

    If ``states`` is None, the total probability mass is returned.

    Examples
    --------
    >>> probability_mass({"00": 75, "11": 25})
    1.0

    >>> probability_mass({"00": 75, "11": 25}, {"00"})
    0.75
    """

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(counts)

    if states is None:
        return sum(probabilities.values())

    state_set = set(states)

    return sum(
        probability
        for state, probability in probabilities.items()
        if state in state_set
    )


def dominant_state(
    counts: Counts,
) -> str | None:
    """
    Return the most frequently measured state.

    Returns None for an empty distribution.
    """

    if not counts:
        return None

    _validate_counts(counts)

    return max(
        counts,
        key=counts.get,
    )


def dominant_probability(
    counts: Counts,
) -> float:
    """
    Return the probability of the dominant measurement state.

    Returns 0.0 for an empty distribution.
    """

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(counts)

    state = dominant_state(counts)

    if state is None:
        return 0.0

    return probabilities[state]


def shannon_entropy(
    counts: Counts,
) -> float:
    """
    Calculate Shannon entropy in bits.

    H(X) = -sum(p(x) log2(p(x)))

    Empty distributions return 0.0.
    """

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(counts)

    return -sum(
        probability * math.log2(probability)
        for probability in probabilities.values()
        if probability > 0.0
    )


def maximum_entropy(
    counts: Counts,
) -> float:
    """
    Return the maximum possible Shannon entropy for the
    number of observed states.

    H_max = log2(N)

    where N is the number of unique observed states.
    """

    if not counts:
        return 0.0

    return math.log2(len(counts))


def normalized_entropy(
    counts: Counts,
) -> float:
    """
    Return Shannon entropy normalized to [0, 1].

    normalized_H = H / H_max

    For a single observed state, normalized entropy is 0.0.
    """

    if not counts:
        return 0.0

    entropy = shannon_entropy(counts)
    maximum = maximum_entropy(counts)

    if maximum == 0.0:
        return 0.0

    return entropy / maximum


def probability_mass_error(
    counts: Counts,
) -> float:
    """
    Return the absolute deviation of probability mass from 1.0.
    """

    if not counts:
        return 0.0

    return abs(
        probability_mass(counts) - 1.0
    )


def measurement_summary(
    counts: Counts,
) -> dict[str, float | int | str | None]:
    """
    Return a compact statistical summary of a measurement distribution.

    Returned fields
    ---------------
    shots
        Total number of measurements.

    unique_states
        Number of distinct observed states.

    dominant_state
        Most frequently observed state.

    dominant_probability
        Probability of the dominant state.

    shannon_entropy_bits
        Shannon entropy in bits.

    maximum_entropy_bits
        Maximum entropy for the observed state space.

    normalized_entropy
        Entropy normalized to [0, 1].

    probability_mass
        Sum of all probabilities.

    probability_mass_error
        Absolute error from probability mass 1.0.

    Empty distributions return a valid zero-valued summary.
    """

    if not counts:
        return {
            "shots": 0,
            "unique_states": 0,
            "dominant_state": None,
            "dominant_probability": 0.0,
            "shannon_entropy_bits": 0.0,
            "maximum_entropy_bits": 0.0,
            "normalized_entropy": 0.0,
            "probability_mass": 0.0,
            "probability_mass_error": 0.0,
        }

    _validate_counts(counts)

    return {
        "shots": total_shots(counts),
        "unique_states": len(counts),
        "dominant_state": dominant_state(counts),
        "dominant_probability": dominant_probability(counts),
        "shannon_entropy_bits": shannon_entropy(counts),
        "maximum_entropy_bits": maximum_entropy(counts),
        "normalized_entropy": normalized_entropy(counts),
        "probability_mass": probability_mass(counts),
        "probability_mass_error": probability_mass_error(counts),
    }


__all__ = [
    "Counts",
    "total_shots",
    "measurement_probabilities",
    "probability_mass",
    "dominant_state",
    "dominant_probability",
    "shannon_entropy",
    "maximum_entropy",
    "normalized_entropy",
    "probability_mass_error",
    "measurement_summary",
]