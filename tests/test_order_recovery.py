from qattack.analysis.order import (
    candidate_order_from_phase,
    recover_order_from_phase,
    verify_order,
)

from qattack.analysis.phase import (
    bitstring_to_phase,
)

from qattack.quantum.phase_estimation import (
    dominant_phase,
    run_qpe,
)


def test_phase_010_is_one_quarter():

    phase = bitstring_to_phase(
        "010"
    )

    assert phase == 0.25


def test_phase_010_gives_candidate_order_four():

    phase = bitstring_to_phase(
        "010"
    )

    candidate = candidate_order_from_phase(
        phase,
        max_denominator=15,
    )

    assert candidate == 4


def test_order_four_is_valid_for_2_mod_15():

    assert verify_order(
        a=2,
        r=4,
        n=15,
    )


def test_order_two_is_not_valid():

    assert not verify_order(
        a=2,
        r=2,
        n=15,
    )


def test_phase_recovers_order_four():

    phase = bitstring_to_phase(
        "010"
    )

    order = recover_order_from_phase(
        a=2,
        n=15,
        phase=phase,
    )

    assert order == 4


def test_qpe_measurement_recovers_order():

    counts = run_qpe(
        eigen_index=1,
        shots=1024,
    )

    phase = dominant_phase(
        counts
    )

    order = recover_order_from_phase(
        a=2,
        n=15,
        phase=phase,
    )

    assert order == 4