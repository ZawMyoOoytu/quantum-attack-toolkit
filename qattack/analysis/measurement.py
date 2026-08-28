from __future__ import annotations

from math import log2
from typing import Mapping


def measurement_probabilities(
    counts: Mapping[str, int],
) -> dict[str, float]:
    """
    Convert measurement counts into probabilities.

    Parameters
    ----------
    counts:
        Mapping of measurement bitstrings to counts.

    Returns
    -------
    dict[str, float]
        Normalized probability distribution.
    """

    if not counts:
        return {}

    total = sum(counts.values())

    if total <= 0:
        raise ValueError("Measurement counts must have a positive total.")

    if any(count < 0 for count in counts.values()):
        raise ValueError("Measurement counts cannot be negative.")

    return {
        state: count / total
        for state, count in counts.items()
    }


def dominant_probability(
    counts: Mapping[str, int],
) -> float:
    """
    Return the probability of the most frequently
    observed measurement state.
    """

    probabilities = measurement_probabilities(counts)

    if not probabilities:
        return 0.0

    return max(probabilities.values())


def shannon_entropy(
    counts: Mapping[str, int],
) -> float:
    """
    Calculate Shannon entropy in bits.

    H(X) = -sum(p_i * log2(p_i))
    """

    probabilities = measurement_probabilities(counts)

    entropy = 0.0

    for probability in probabilities.values():
        if probability > 0.0:
            entropy -= probability * log2(probability)

    return entropy


def probability_mass(
    counts: Mapping[str, int],
    states: set[str] | list[str] | tuple[str, ...],
) -> float:
    """
    Calculate the total probability mass assigned
    to a selected set of measurement states.
    """

    probabilities = measurement_probabilities(counts)

    return sum(
        probabilities.get(state, 0.0)
        for state in states
    )


def measurement_summary(
    counts: Mapping[str, int],
) -> dict[str, float | int]:
    """
    Return basic measurement-distribution metrics.
    """

    probabilities = measurement_probabilities(counts)

    return {
        "shots": sum(counts.values()),
        "unique_states": len(counts),
        "dominant_probability": dominant_probability(counts),
        "shannon_entropy_bits": shannon_entropy(counts),
    }