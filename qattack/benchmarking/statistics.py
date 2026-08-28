from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Sequence


@dataclass
class BenchmarkStatistics:
    """
    Statistical analysis for repeated benchmark runs.

    This class intentionally does not import BenchmarkRun directly.
    It works with BenchmarkRun-compatible objects through their
    public attributes.

    This avoids circular-import problems between:

        runner.py
        metrics.py
        statistics.py
    """

    # ---------------------------------------------------------
    # Benchmark identity
    # ---------------------------------------------------------

    attack: str

    target: str

    target_type: str

    size: int

    # ---------------------------------------------------------
    # Experiment configuration
    # ---------------------------------------------------------

    shots: int

    trials: int

    # ---------------------------------------------------------
    # Trial counts
    # ---------------------------------------------------------

    successful_trials: int

    failed_trials: int

    successful_order_recoveries: int

    failed_order_recoveries: int

    successful_factor_recoveries: int

    failed_factor_recoveries: int

    # ---------------------------------------------------------
    # Rates
    # ---------------------------------------------------------

    success_rate: float

    order_recovery_rate: float

    factor_recovery_rate: float

    # ---------------------------------------------------------
    # Timing / performance
    # ---------------------------------------------------------

    mean_elapsed_seconds: float

    # ---------------------------------------------------------
    # Quantum execution statistics
    # ---------------------------------------------------------

    mean_success_probability: float

    mean_circuit_depth: float

    mean_gate_count: float

    logical_qubits: int

    # =========================================================
    # Summary
    # =========================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return a JSON-friendly statistical summary.
        """

        return {
            # ---------------------------------------------
            # Benchmark identity
            # ---------------------------------------------

            "attack": self.attack,

            "target": self.target,

            "target_type": self.target_type,

            "size": self.size,

            # ---------------------------------------------
            # Experiment configuration
            # ---------------------------------------------

            "shots": self.shots,

            "trials": self.trials,

            # ---------------------------------------------
            # Trial counts
            # ---------------------------------------------

            "successful_trials": (
                self.successful_trials
            ),

            "failed_trials": (
                self.failed_trials
            ),

            "successful_order_recoveries": (
                self.successful_order_recoveries
            ),

            "failed_order_recoveries": (
                self.failed_order_recoveries
            ),

            "successful_factor_recoveries": (
                self.successful_factor_recoveries
            ),

            "failed_factor_recoveries": (
                self.failed_factor_recoveries
            ),

            # ---------------------------------------------
            # Rates
            # ---------------------------------------------

            "success_rate": (
                self.success_rate
            ),

            "order_recovery_rate": (
                self.order_recovery_rate
            ),

            "factor_recovery_rate": (
                self.factor_recovery_rate
            ),

            # ---------------------------------------------
            # Timing
            # ---------------------------------------------

            "mean_elapsed_seconds": (
                self.mean_elapsed_seconds
            ),

            # ---------------------------------------------
            # Quantum execution
            # ---------------------------------------------

            "mean_success_probability": (
                self.mean_success_probability
            ),

            "mean_circuit_depth": (
                self.mean_circuit_depth
            ),

            "mean_gate_count": (
                self.mean_gate_count
            ),

            "logical_qubits": (
                self.logical_qubits
            ),
        }


# =============================================================
# Helper functions
# =============================================================


def _metric(
    run: Any,
    name: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a metric from a benchmark run.

    BenchmarkRun stores benchmark-specific information
    inside the `metrics` dictionary.
    """

    metrics = getattr(
        run,
        "metrics",
        {},
    )

    if not isinstance(
        metrics,
        dict,
    ):
        return default

    return metrics.get(
        name,
        default,
    )


def _order_recovered(
    run: Any,
) -> bool:
    """
    Determine whether a valid quantum period/order
    was recovered.

    Primary condition:

        recovered_order is not None

    If `order_verified` is available, it must also be True.
    """

    recovered_order = _metric(
        run,
        "recovered_order",
        None,
    )

    if recovered_order is None:
        return False

    order_verified = _metric(
        run,
        "order_verified",
        None,
    )

    if order_verified is None:
        return True

    return bool(
        order_verified
    )


def _factor_recovered(
    run: Any,
) -> bool:
    """
    Determine whether non-trivial factors were recovered.

    For the N=15 benchmark the expected value is:

        factors = (3, 5)

    A factor recovery is considered successful whenever
    the `factors` metric is not None.

    Empty factor collections are treated as failure.
    """

    factors = _metric(
        run,
        "factors",
        None,
    )

    if factors is None:
        return False

    if isinstance(
        factors,
        (tuple, list, set),
    ):
        return len(factors) > 0

    return True


# =============================================================
# Main statistical calculation
# =============================================================


def calculate_statistics(
    runs: Sequence[Any],
) -> BenchmarkStatistics:
    """
    Calculate aggregate statistics from repeated benchmark runs.

    Parameters
    ----------
    runs:
        Sequence of BenchmarkRun-compatible objects.

    Returns
    -------
    BenchmarkStatistics
        Aggregate statistics for the supplied runs.

    Raises
    ------
    ValueError
        If the supplied sequence is empty.
    """

    if not runs:
        raise ValueError(
            "At least one benchmark run is required."
        )

    # ---------------------------------------------------------
    # First run defines benchmark identity/configuration.
    # ---------------------------------------------------------

    first = runs[0]

    trials = len(
        runs
    )

    shots = int(
        getattr(
            first,
            "shots",
            0,
        )
    )

    # ---------------------------------------------------------
    # Benchmark identity
    #
    # BenchmarkRun historically used `attack`.
    # Some versions may expose `attack_name`.
    # ---------------------------------------------------------

    attack = getattr(
        first,
        "attack",
        None,
    )

    if attack is None:
        attack = getattr(
            first,
            "attack_name",
            "unknown",
        )

    target = getattr(
        first,
        "target",
        "unknown",
    )

    target_type = getattr(
        first,
        "target_type",
        "unknown",
    )

    size = int(
        getattr(
            first,
            "size",
            0,
        )
    )

    # ---------------------------------------------------------
    # Successful benchmark trials
    # ---------------------------------------------------------

    successful_trials = sum(
        1
        for run in runs
        if bool(
            getattr(
                run,
                "success",
                False,
            )
        )
    )

    failed_trials = (
        trials
        - successful_trials
    )

    # ---------------------------------------------------------
    # Order recovery
    # ---------------------------------------------------------

    successful_order_recoveries = sum(
        1
        for run in runs
        if _order_recovered(run)
    )

    failed_order_recoveries = (
        trials
        - successful_order_recoveries
    )

    # ---------------------------------------------------------
    # Factor recovery
    # ---------------------------------------------------------

    successful_factor_recoveries = sum(
        1
        for run in runs
        if _factor_recovered(run)
    )

    failed_factor_recoveries = (
        trials
        - successful_factor_recoveries
    )

    # ---------------------------------------------------------
    # Rates
    # ---------------------------------------------------------

    success_rate = (
        successful_trials
        / trials
    )

    order_recovery_rate = (
        successful_order_recoveries
        / trials
    )

    factor_recovery_rate = (
        successful_factor_recoveries
        / trials
    )

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    elapsed_values = [
        float(
            getattr(
                run,
                "elapsed_seconds",
                0.0,
            )
        )
        for run in runs
    ]

    mean_elapsed_seconds = mean(
        elapsed_values
    )

    # ---------------------------------------------------------
    # Success probability
    # ---------------------------------------------------------

    success_probability_values = [
        float(
            getattr(
                run,
                "success_probability",
                0.0,
            )
        )
        for run in runs
    ]

    mean_success_probability = mean(
        success_probability_values
    )

    # ---------------------------------------------------------
    # Circuit depth
    # ---------------------------------------------------------

    circuit_depth_values = [
        float(
            getattr(
                run,
                "circuit_depth",
                0,
            )
        )
        for run in runs
    ]

    mean_circuit_depth = mean(
        circuit_depth_values
    )

    # ---------------------------------------------------------
    # Gate count
    # ---------------------------------------------------------

    gate_count_values = [
        float(
            getattr(
                run,
                "gate_count",
                0,
            )
        )
        for run in runs
    ]

    mean_gate_count = mean(
        gate_count_values
    )

    # ---------------------------------------------------------
    # Logical qubits
    #
    # Logical qubits should normally be constant for the
    # same benchmark. Use the maximum observed value so the
    # summary remains robust if compatible benchmark objects
    # vary slightly.
    # ---------------------------------------------------------

    logical_qubit_values = [
        int(
            getattr(
                run,
                "logical_qubits",
                0,
            )
        )
        for run in runs
    ]

    logical_qubits = max(
        logical_qubit_values
    )

    # ---------------------------------------------------------
    # Construct result
    # ---------------------------------------------------------

    return BenchmarkStatistics(
        # Benchmark identity
        attack=str(
            attack
        ),

        target=str(
            target
        ),

        target_type=str(
            target_type
        ),

        size=size,

        # Configuration
        shots=shots,

        trials=trials,

        # Trial counts
        successful_trials=(
            successful_trials
        ),

        failed_trials=(
            failed_trials
        ),

        successful_order_recoveries=(
            successful_order_recoveries
        ),

        failed_order_recoveries=(
            failed_order_recoveries
        ),

        successful_factor_recoveries=(
            successful_factor_recoveries
        ),

        failed_factor_recoveries=(
            failed_factor_recoveries
        ),

        # Rates
        success_rate=(
            success_rate
        ),

        order_recovery_rate=(
            order_recovery_rate
        ),

        factor_recovery_rate=(
            factor_recovery_rate
        ),

        # Timing
        mean_elapsed_seconds=(
            mean_elapsed_seconds
        ),

        # Quantum execution
        mean_success_probability=(
            mean_success_probability
        ),

        mean_circuit_depth=(
            mean_circuit_depth
        ),

        mean_gate_count=(
            mean_gate_count
        ),

        logical_qubits=(
            logical_qubits
        ),
    )


# =============================================================
# Compatibility API
# =============================================================


def analyze_benchmark_runs(
    runs: Sequence[Any],
) -> BenchmarkStatistics:
    """
    Analyze repeated benchmark runs.

    This is the public compatibility API used by
    tests/test_statistics.py.
    """

    return calculate_statistics(
        runs
    )