"""
Phase-analysis utilities.

Educational/research benchmark only.
"""

from __future__ import annotations

from fractions import Fraction


def bitstring_to_phase(
    bitstring: str,
) -> float:
    """
    Convert a binary phase-register measurement
    into a phase in [0, 1).

    Example:

        010 -> 2 / 8 = 0.25
    """

    if not bitstring:
        raise ValueError(
            "bitstring cannot be empty"
        )

    if any(
        bit not in "01"
        for bit in bitstring
    ):
        raise ValueError(
            "bitstring must contain only 0 and 1"
        )

    value = int(
        bitstring,
        2,
    )

    denominator = 2 ** len(bitstring)

    return value / denominator


def phase_to_fraction(
    phase: float,
    max_denominator: int,
) -> Fraction:
    """
    Convert a phase into its best rational approximation.
    """

    if not 0.0 <= phase < 1.0:
        raise ValueError(
            "phase must be in [0, 1)"
        )

    if max_denominator <= 0:
        raise ValueError(
            "max_denominator must be positive"
        )

    return Fraction(
        phase
    ).limit_denominator(
        max_denominator
    )


def recover_order_candidates(
    phase: float,
    max_denominator: int = 15,
) -> list[int]:
    """
    Generate candidate order denominators from a measured phase.

    The phase is approximated as a rational number and the
    denominator is returned as the primary candidate.

    Example:

        phase = 0.25
        0.25 = 1/4

        candidates = [4]
    """

    fraction = phase_to_fraction(
        phase,
        max_denominator,
    )

    denominator = fraction.denominator

    if denominator == 1:
        return [1]

    return [denominator]