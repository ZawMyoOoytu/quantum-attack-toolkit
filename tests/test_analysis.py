from qattack.analysis.factor import derive_factors
from qattack.analysis.order import recover_order, verify_order
from qattack.analysis.phase import (
    bitstring_to_phase,
    phase_to_fraction,
    recover_order_candidates,
)


def test_phase_binary_conversion():
    assert bitstring_to_phase("0000") == 0.0
    assert bitstring_to_phase("0100") == 0.25
    assert bitstring_to_phase("1000") == 0.5


def test_phase_fraction():
    result = phase_to_fraction(
        0.25,
        15,
    )

    assert result.numerator == 1
    assert result.denominator == 4


def test_candidate_order():
    candidates = recover_order_candidates(
        phase=0.25,
        max_denominator=15,
    )

    assert candidates == [4]


def test_order_verification():
    assert verify_order(
        a=2,
        r=4,
        n=15,
    )

    assert not verify_order(
        a=2,
        r=2,
        n=15,
    )


def test_order_recovery():
    candidates = [2, 4, 8]

    result = recover_order(
        a=2,
        n=15,
        candidates=candidates,
    )

    assert result == 4


def test_factor_derivation():
    result = derive_factors(
        a=2,
        r=4,
        n=15,
    )

    assert result == (3, 5)