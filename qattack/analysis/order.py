"""
Order-recovery utilities for the N=15 research benchmark.

Educational/research benchmark only.
No real cryptographic keys, credentials, or third-party
systems are accessed.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable


def candidate_order_from_phase(
    phase: float,
    max_denominator: int = 15,
) -> int:
    """
    Convert a measured phase into a denominator candidate.

    Example:

        phase = 0.25
        0.25 = 1/4

        candidate = 4
    """

    if not 0.0 <= phase < 1.0:
        raise ValueError(
            "phase must be in [0, 1)"
        )

    if max_denominator <= 0:
        raise ValueError(
            "max_denominator must be positive"
        )

    fraction = Fraction(
        phase
    ).limit_denominator(
        max_denominator
    )

    return fraction.denominator


def verify_order(
    a: int,
    r: int,
    n: int,
) -> bool:
    """
    Verify that r is the multiplicative order of a modulo n.
    """

    if not isinstance(a, int):
        return False

    if not isinstance(r, int):
        return False

    if not isinstance(n, int):
        return False

    if a <= 0:
        return False

    if r <= 0:
        return False

    if n <= 1:
        return False

    if pow(a, r, n) != 1:
        return False

    # r must be the smallest positive exponent.
    for k in range(1, r):
        if pow(a, k, n) == 1:
            return False

    return True


def recover_order(
    a: int,
    n: int,
    candidates: Iterable[int] | None = None,
) -> int | None:
    """
    Recover the first verified order from a list of candidates.

    This preserves the original project API:

        recover_order(
            a=2,
            n=15,
            candidates=[2, 4, 8],
        )

    For N=15 and a=2:

        r=2  -> invalid
        r=4  -> valid
        r=8  -> not the minimal order

    Therefore:

        result = 4
    """

    if candidates is None:
        return None

    for candidate in candidates:

        if verify_order(
            a=a,
            r=candidate,
            n=n,
        ):
            return candidate

    return None


def recover_order_from_phase(
    a: int,
    n: int,
    phase: float,
    max_denominator: int = 15,
) -> int | None:
    """
    Convert a measured phase into a candidate order and
    verify it.

    Example:

        phase = 0.25

        0.25 -> 1/4 -> candidate r=4

        verify(2, 4, 15) -> True
    """

    candidate = candidate_order_from_phase(
        phase=phase,
        max_denominator=max_denominator,
    )

    return recover_order(
        a=a,
        n=n,
        candidates=[candidate],
    )