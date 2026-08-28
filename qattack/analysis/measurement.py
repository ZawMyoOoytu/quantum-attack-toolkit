
from __future__ import annotations

"""
Measurement-distribution analysis utilities.

This module provides classical statistical analysis for quantum
measurement results represented as Qiskit-style counts.

The module does not execute quantum circuits.

Typical workflow:

    Quantum circuit
          ↓
    Aer / QPU execution
          ↓
    measurement counts
          ↓
    measurement.py
          ↓
    probability / entropy / distribution statistics
          ↓
    noise benchmark analysis


Supported analysis
------------------

- Total measurement shots
- Number of unique states
- Measurement probabilities
- Dominant measurement state
- Dominant probability
- Shannon entropy
- Maximum entropy
- Normalized entropy
- Probability mass
- Probability-mass validation
- State-specific probability
- Top measured states
"""


from math import log2
from numbers import Integral, Real
from typing import Mapping


# ============================================================================
# Type aliases
# ============================================================================

Counts = Mapping[str, int]


# ============================================================================
# Internal validation
# ============================================================================


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
        Mapping of binary measurement states to integer counts.

    allow_empty:
        If True, an empty mapping is accepted.

    Raises
    ------
    TypeError
        If counts, states, or count values have invalid types.

    ValueError
        If a state is invalid, a count is negative, or the total
        number of shots is zero.
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
                "Measurement states must be strings."
            )

        if not state:
            raise ValueError(
                "Measurement states must not be empty."
            )

        if any(
            bit not in {"0", "1"}
            for bit in state
        ):
            raise ValueError(
                "Measurement states must be binary bitstrings."
            )

        if not isinstance(count, Integral):
            raise TypeError(
                "Measurement counts must be integers."
            )

        if count < 0:
            raise ValueError(
                "Measurement counts cannot be negative."
            )

    total = sum(
        int(count)
        for count in counts.values()
    )

    if total <= 0:
        raise ValueError(
            "Total measurement shots must be positive."
        )


def _validate_tolerance(
    tolerance: float,
) -> None:
    """
    Validate a numerical tolerance.
    """

    if not isinstance(tolerance, Real):
        raise TypeError(
            "tolerance must be a real number."
        )

    if float(tolerance) < 0.0:
        raise ValueError(
            "tolerance must be non-negative."
        )


# ============================================================================
# Basic statistics
# ============================================================================


def total_shots(
    counts: Counts,
) -> int:
    """
    Return the total number of measurement shots.

    Examples
    --------
    >>> total_shots({"00": 50, "11": 50})
    100
    """

    if not counts:
        return 0

    _validate_counts(counts)

    return int(
        sum(counts.values())
    )


def unique_states(
    counts: Counts,
) -> int:
    """
    Return the number of distinct measurement states.

    Examples
    --------
    >>> unique_states({"00": 50, "11": 50})
    2
    """

    if not counts:
        return 0

    _validate_counts(counts)

    return len(counts)


# ============================================================================
# Measurement probabilities
# ============================================================================


def measurement_probabilities(
    counts: Counts,
) -> dict[str, float]:
    """
    Convert measurement counts into normalized probabilities.

    Empty distributions return an empty dictionary.

    Examples
    --------
    >>> measurement_probabilities(
    ...     {"00": 75, "11": 25}
    ... )
    {'00': 0.75, '11': 0.25}
    """

    if not counts:
        return {}

    _validate_counts(counts)

    shots = sum(
        int(count)
        for count in counts.values()
    )

    if shots <= 0:
        return {}

    return {
        state: float(count) / float(shots)
        for state, count in counts.items()
    }


# ============================================================================
# Dominant measurement state
# ============================================================================


def dominant_state(
    counts: Counts,
) -> str | None:
    """
    Return the most frequently measured state.

    Empty distributions return None.

    If multiple states have the same maximum count, the first
    state according to mapping iteration order is returned.

    Examples
    --------
    >>> dominant_state({"00": 75, "11": 25})
    '00'
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
    Return the probability of the most frequently measured state.

    Empty distributions return 0.0.

    Examples
    --------
    >>> dominant_probability({"00": 75, "11": 25})
    0.75
    """

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(
        counts
    )

    if not probabilities:
        return 0.0

    return float(
        max(probabilities.values())
    )


# ============================================================================
# Shannon entropy
# ============================================================================


def shannon_entropy(
    counts: Counts,
    *,
    base: float = 2.0,
) -> float:
    """
    Calculate Shannon entropy of a measurement distribution.

    Formula
    -------

        H(X) = -Σ p(x) log_b p(x)

    With base=2, entropy is measured in bits.

    Parameters
    ----------
    counts:
        Measurement counts.

    base:
        Logarithm base.

        base=2:
            entropy in bits.

        base=e:
            entropy in nats.

    Empty distributions return 0.0.

    Examples
    --------
    >>> shannon_entropy({"00": 50, "11": 50})
    1.0
    """

    if not isinstance(base, Real):
        raise TypeError(
            "base must be a real number."
        )

    base = float(base)

    if base <= 0.0 or base == 1.0:
        raise ValueError(
            "base must be positive and different from 1."
        )

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(
        counts
    )

    entropy = 0.0

    log_base = log2(base)

    for probability in probabilities.values():

        if probability <= 0.0:
            continue

        entropy -= (
            probability
            * log2(probability)
            / log_base
        )

    return float(entropy)


def shannon_entropy_bits(
    counts: Counts,
) -> float:
    """
    Calculate Shannon entropy in bits.

    This is equivalent to:

        shannon_entropy(counts, base=2)
    """

    return shannon_entropy(
        counts,
        base=2.0,
    )


# ============================================================================
# Probability mass
# ============================================================================


def probability_mass(
    counts: Counts,
    states: set[str] | None = None,
) -> float:
    """
    Calculate probability mass.

    Parameters
    ----------
    counts:
        Measurement counts.

    states:
        Optional collection of measurement states.

        If None:
            return total probability mass.

        If provided:
            return the combined probability of those states.

    Examples
    --------
    >>> counts = {"00": 75, "11": 25}

    >>> probability_mass(counts)
    1.0

    >>> probability_mass(counts, {"00"})
    0.75

    >>> probability_mass(counts, {"00", "11"})
    1.0
    """

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(
        counts
    )

    if states is None:
        return float(
            sum(probabilities.values())
        )

    selected_states = set(states)

    return float(
        sum(
            probabilities.get(
                state,
                0.0,
            )
            for state in selected_states
        )
    )


def probability_mass_error(
    counts: Counts,
) -> float:
    """
    Return the absolute deviation of total probability mass from 1.

    Empty distributions return 0.0.

    Examples
    --------
    >>> probability_mass_error({"00": 75, "11": 25})
    0.0
    """

    if not counts:
        return 0.0

    return abs(
        probability_mass(counts) - 1.0
    )


def is_normalized(
    counts: Counts,
    *,
    tolerance: float = 1e-12,
) -> bool:
    """
    Check whether a measurement distribution is normalized.

    Empty distributions are considered trivially normalized.

    Parameters
    ----------
    counts:
        Measurement counts.

    tolerance:
        Maximum allowed deviation from probability mass 1.0.
    """

    _validate_tolerance(
        tolerance
    )

    if not counts:
        return True

    return (
        probability_mass_error(counts)
        <= float(tolerance)
    )


# ============================================================================
# Entropy normalization
# ============================================================================


def maximum_entropy_bits(
    counts: Counts,
) -> float:
    """
    Return the maximum entropy over the observed states.

    For M observed states:

        H_max = log2(M)

    Empty distributions return 0.0.

    Note
    ----
    This is the maximum entropy over the observed support, not
    necessarily the full Hilbert-space dimension.
    """

    states = unique_states(counts)

    if states <= 0:
        return 0.0

    return float(
        log2(states)
    )


def normalized_entropy(
    counts: Counts,
) -> float:
    """
    Return Shannon entropy normalized to [0, 1].

    Formula
    -------

        H_normalized = H / H_max

    where:

        H_max = log2(number of observed states)

    Interpretation
    --------------

        0:
            Highly concentrated distribution.

        1:
            Approximately uniform distribution over observed states.

    Empty distributions return 0.0.
    """

    if not counts:
        return 0.0

    entropy = shannon_entropy_bits(
        counts
    )

    maximum = maximum_entropy_bits(
        counts
    )

    if maximum <= 0.0:
        return 0.0

    return float(
        entropy / maximum
    )


# ============================================================================
# State-specific probability
# ============================================================================


def state_probability(
    counts: Counts,
    state: str,
) -> float:
    """
    Return the probability of a specific measurement state.

    If the state is not present, return 0.0.

    Examples
    --------
    >>> state_probability(
    ...     {"00": 75, "11": 25},
    ...     "00",
    ... )
    0.75
    """

    if not isinstance(state, str):
        raise TypeError(
            "state must be a string."
        )

    if not counts:
        return 0.0

    probabilities = measurement_probabilities(
        counts
    )

    return float(
        probabilities.get(
            state,
            0.0,
        )
    )


# ============================================================================
# Top measurement states
# ============================================================================


def top_states(
    counts: Counts,
    *,
    limit: int = 5,
) -> list[tuple[str, int, float]]:
    """
    Return the most frequently measured states.

    Parameters
    ----------
    counts:
        Measurement counts.

    limit:
        Maximum number of states.

    Returns
    -------
    list[tuple[str, int, float]]

        Each tuple contains:

            (
                state,
                count,
                probability,
            )

    Empty distributions return [].

    Examples
    --------
    >>> top_states(
    ...     {"00": 75, "11": 25},
    ...     limit=1,
    ... )
    [('00', 75, 0.75)]
    """

    if not isinstance(limit, Integral):
        raise TypeError(
            "limit must be an integer."
        )

    if limit <= 0:
        raise ValueError(
            "limit must be positive."
        )

    if not counts:
        return []

    _validate_counts(counts)

    probabilities = measurement_probabilities(
        counts
    )

    ordered = sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        (
            state,
            int(count),
            float(probabilities[state]),
        )
        for state, count in ordered[:limit]
    ]


# ============================================================================
# Uniform distribution entropy
# ============================================================================


def uniform_entropy_bits(
    number_of_states: int,
) -> float:
    """
    Return entropy of a uniform distribution over M states.

    Formula:

        H_uniform = log2(M)

    Examples
    --------
    >>> uniform_entropy_bits(16)
    4.0
    """

    if not isinstance(
        number_of_states,
        Integral,
    ):
        raise TypeError(
            "number_of_states must be an integer."
        )

    if number_of_states <= 0:
        raise ValueError(
            "number_of_states must be positive."
        )

    return float(
        log2(number_of_states)
    )


# ============================================================================
# Compact measurement summary
# ============================================================================


def measurement_summary(
    counts: Counts,
) -> dict[str, float | int | str | None]:
    """
    Produce a compact statistical summary.

    Returned fields
    ---------------

    shots
        Total number of measurement shots.

    unique_states
        Number of distinct observed states.

    dominant_state
        Most frequently measured state.

    dominant_probability
        Probability of the dominant state.

    shannon_entropy_bits
        Shannon entropy in bits.

    maximum_entropy_bits
        Maximum entropy over the observed support.

    normalized_entropy
        Entropy normalized to [0, 1].

    probability_mass
        Total probability mass.

    probability_mass_error
        Absolute deviation from 1.

    Empty distributions return a zero-valued summary.
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

    probabilities = measurement_probabilities(
        counts
    )

    dominant = dominant_state(
        counts
    )

    entropy = shannon_entropy_bits(
        counts
    )

    maximum = maximum_entropy_bits(
        counts
    )

    normalized = (
        entropy / maximum
        if maximum > 0.0
        else 0.0
    )

    mass = float(
        sum(probabilities.values())
    )

    return {
        "shots": total_shots(counts),

        "unique_states": unique_states(counts),

        "dominant_state": dominant,

        "dominant_probability": (
            float(
                probabilities[dominant]
            )
            if dominant is not None
            else 0.0
        ),

        "shannon_entropy_bits": (
            float(entropy)
        ),

        "maximum_entropy_bits": (
            float(maximum)
        ),

        "normalized_entropy": (
            float(normalized)
        ),

        "probability_mass": mass,

        "probability_mass_error": abs(
            mass - 1.0
        ),
    }


# ============================================================================
# Public API
# ============================================================================


__all__ = [
    "Counts",
    "total_shots",
    "unique_states",
    "measurement_probabilities",
    "dominant_state",
    "dominant_probability",
    "shannon_entropy",
    "shannon_entropy_bits",
    "probability_mass",
    "probability_mass_error",
    "is_normalized",
    "maximum_entropy_bits",
    "normalized_entropy",
    "state_probability",
    "top_states",
    "uniform_entropy_bits",
    "measurement_summary",
]

