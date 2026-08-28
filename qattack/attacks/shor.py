
from __future__ import annotations

from math import gcd

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFTGate
from qiskit_aer import AerSimulator

from qattack.core.attack import QuantumAttack
from qattack.core.result import AttackResult
from qattack.core.target import Target

from qattack.analysis.factor import derive_factors
from qattack.analysis.order import (
    recover_order,
    verify_order,
)
from qattack.analysis.phase import (
    bitstring_to_phase,
    recover_order_candidates,
)
from qattack.quantum.modular import (
    controlled_modular_power_2,
)
from qattack.quantum.noise import (
    NoiseConfig,
    build_noise_model,
)


class ShorAttack(QuantumAttack):
    """
    Small-scale Shor research benchmark.

    Supported benchmark:

        N = 15
        a = 2

    Quantum workflow:

        |1>
          ↓
        Controlled modular exponentiation
          ↓
        Quantum Phase Estimation
          ↓
        Inverse QFT
          ↓
        Measurement
          ↓
        Phase extraction
          ↓
        Continued fractions
          ↓
        Candidate order recovery
          ↓
        Order verification
          ↓
        Factor derivation

    Noise workflow:

        NoiseConfig
             ↓
        NoiseModel
             ↓
        AerSimulator
             ↓
        Noisy execution
             ↓
        Measurement
             ↓
        Order recovery
             ↓
        Factor recovery

    Scope:

        - Local Qiskit Aer simulation
        - Toy integer factorization
        - Quantum period-finding study
        - Configurable simulator shots
        - Configurable noise models
        - Benchmarking and reporting
        - No credential/key extraction
        - No third-party system access
    """

    name = "shor"
    target_type = "rsa"

    # -------------------------------------------------
    # Benchmark constants
    # -------------------------------------------------

    DEFAULT_SHOTS = 1024
    COUNTING_QUBITS = 4
    WORK_QUBITS = 4

    EXPECTED_ORDER_N15_A2 = 4
    EXPECTED_FACTORS_N15 = (3, 5)

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def validate(
        self,
        target: Target,
    ) -> None:
        """
        Validate that the supplied target is compatible
        with this research implementation.
        """

        if target.target_type.lower() != "rsa":
            raise ValueError(
                "ShorAttack requires an RSA-style target."
            )

        if target.size != 15:
            raise ValueError(
                "This implementation currently supports "
                "only the N=15 research benchmark."
            )

    # -------------------------------------------------
    # Main execution
    # -------------------------------------------------

    def run(
        self,
        target: Target,
        shots: int = DEFAULT_SHOTS,
        noise_config: NoiseConfig | None = None,
    ) -> AttackResult:
        """
        Execute the N=15 Shor research benchmark.

        Parameters
        ----------
        target:
            RSA-style toy target.

        shots:
            Number of Aer simulator shots.

        noise_config:
            Optional noise configuration.

            None:
                Ideal Aer simulation.

            NoiseConfig(model="ideal"):
                Ideal Aer simulation.

            NoiseConfig(
                model="depolarizing",
                depolarizing_probability=0.01,
            ):
                Depolarizing-noise simulation.

            NoiseConfig(
                model="readout",
                readout_probability=0.02,
            ):
                Readout-noise simulation.

            NoiseConfig(
                model="thermal",
                thermal_t1=100.0,
                thermal_t2=80.0,
                gate_time=0.05,
            ):
                Thermal-relaxation simulation.

        Returns
        -------
        AttackResult
            Standardized benchmark result.
        """

        self.validate(target)

        # -------------------------------------------------
        # Validate shots
        # -------------------------------------------------

        if not isinstance(shots, int):
            raise TypeError(
                "shots must be an integer."
            )

        if shots <= 0:
            raise ValueError(
                "shots must be a positive integer."
            )

        # -------------------------------------------------
        # Normalize noise configuration
        # -------------------------------------------------

        if noise_config is not None:

            if not isinstance(
                noise_config,
                NoiseConfig,
            ):
                raise TypeError(
                    "noise_config must be a "
                    "NoiseConfig instance or None."
                )

        # -------------------------------------------------
        # Benchmark parameters
        # -------------------------------------------------

        n = target.size
        a = 2

        # -------------------------------------------------
        # Noise metadata
        # -------------------------------------------------

        if noise_config is None:

            noise_model_name = "ideal"

            noise_probability = 0.0

        else:

            noise_model_name = (
                noise_config.normalized_model()
            )

            if noise_model_name == "depolarizing":

                noise_probability = float(
                    noise_config.depolarizing_probability
                )

            elif noise_model_name == "readout":

                noise_probability = float(
                    noise_config.readout_probability
                )

            else:

                noise_probability = 0.0

        # -------------------------------------------------
        # Step 1: Classical GCD shortcut
        # -------------------------------------------------

        common_factor = gcd(a, n)

        if common_factor != 1:

            return AttackResult(
                attack_name=self.name,
                target_type=self.target_type,
                success=True,

                logical_qubits=0,
                circuit_depth=0,
                gate_count=0,

                shots=shots,

                success_probability=1.0,

                metrics={
                    "N": n,
                    "a": a,
                    "counts": {},
                    "phases": [],
                    "candidate_orders": [],
                    "recovered_order": None,
                    "order_verified": False,
                    "factors": (
                        common_factor,
                        n // common_factor,
                    ),
                    "expected_order": (
                        self.EXPECTED_ORDER_N15_A2
                    ),
                    "method": (
                        "classical-gcd-shortcut"
                    ),
                    "noise_model": noise_model_name,
                    "noise_probability": (
                        noise_probability
                    ),
                },

                notes=[
                    (
                        "A non-trivial GCD factor "
                        "was found."
                    ),
                    (
                        "Quantum period finding "
                        "was unnecessary."
                    ),
                    (
                        "No real cryptographic key "
                        "was accessed."
                    ),
                ],
            )

        # -------------------------------------------------
        # Step 2: Build order-finding circuit
        # -------------------------------------------------

        circuit = self._build_order_finding_circuit(
            n=n,
            a=a,
        )

        # -------------------------------------------------
        # Step 3: Build noise model
        # -------------------------------------------------

        noise_model = build_noise_model(
            noise_config
        )

        # -------------------------------------------------
        # Step 4: Create Aer simulator
        # -------------------------------------------------

        if noise_model is None:

            simulator = AerSimulator()

        else:

            simulator = AerSimulator(
                noise_model=noise_model
            )

        # -------------------------------------------------
        # Step 5: Transpile circuit
        # -------------------------------------------------

        compiled = transpile(
            circuit,
            simulator,
            optimization_level=1,
        )

        # -------------------------------------------------
        # Step 6: Execute circuit
        # -------------------------------------------------

        job = simulator.run(
            compiled,
            shots=shots,
        )

        result = job.result()

        counts = result.get_counts()

        # -------------------------------------------------
        # Step 7: Convert measurement states to phases
        # -------------------------------------------------

        phases = self._extract_phases(
            counts
        )

        # -------------------------------------------------
        # Step 8: Generate candidate orders
        # -------------------------------------------------

        candidate_orders = []

        for phase in phases:

            candidates = recover_order_candidates(
                phase=phase,
                max_denominator=n,
            )

            candidate_orders.extend(
                candidates
            )

        # -------------------------------------------------
        # Remove duplicate candidate orders
        # -------------------------------------------------

        candidate_orders = list(
            dict.fromkeys(
                candidate_orders
            )
        )

        # -------------------------------------------------
        # Step 9: Recover valid order
        # -------------------------------------------------

        recovered_order = recover_order(
            a=a,
            n=n,
            candidates=candidate_orders,
        )

        # -------------------------------------------------
        # Step 10: Verify recovered order
        # -------------------------------------------------

        order_verified = (
            recovered_order is not None
            and verify_order(
                a,
                recovered_order,
                n,
            )
        )

        # -------------------------------------------------
        # Step 11: Derive factors
        # -------------------------------------------------

        factors = None

        if order_verified:

            factors = derive_factors(
                a=a,
                r=recovered_order,
                n=n,
            )

        # -------------------------------------------------
        # Step 12: Determine benchmark success
        # -------------------------------------------------

        success = (
            factors is not None
            and order_verified
        )

        # -------------------------------------------------
        # Step 13: Return standardized result
        # -------------------------------------------------

        return AttackResult(
            attack_name=self.name,
            target_type=self.target_type,
            success=success,

            logical_qubits=circuit.num_qubits,

            circuit_depth=compiled.depth(),

            gate_count=len(
                compiled.data
            ),

            shots=shots,

            # IMPORTANT:
            #
            # This field represents the benchmark-level
            # success indicator used by the existing
            # framework.
            #
            # It is NOT the probability of an individual
            # measurement outcome.
            success_probability=(
                1.0 if success else 0.0
            ),

            metrics={
                "N": n,
                "a": a,

                "counts": counts,

                "phases": phases,

                "candidate_orders": (
                    candidate_orders
                ),

                "recovered_order": (
                    recovered_order
                ),

                "order_verified": (
                    order_verified
                ),

                "factors": factors,

                "expected_order": (
                    self.EXPECTED_ORDER_N15_A2
                ),

                "expected_factors": (
                    self.EXPECTED_FACTORS_N15
                ),

                "method": (
                    "quantum-period-finding-benchmark"
                ),

                # -----------------------------------------
                # Noise metadata
                # -----------------------------------------

                "noise_model": (
                    noise_model_name
                ),

                "noise_probability": (
                    noise_probability
                ),
            },

            notes=[
                (
                    "Circuit executed using "
                    "Qiskit Aer."
                ),

                (
                    "Controlled modular powers were "
                    "generated as U^(2^j) for QPE."
                ),

                (
                    "Measurement results were "
                    "converted into phases."
                ),

                (
                    "Continued-fraction denominators "
                    "generated candidate orders."
                ),

                (
                    "Candidate orders were "
                    "classically verified."
                ),

                (
                    "Factors were derived only after "
                    "valid order recovery."
                ),

                (
                    f"Noise model: "
                    f"{noise_model_name}."
                ),

                (
                    "This is an N=15 research "
                    "benchmark."
                ),

                (
                    "No real cryptographic key "
                    "was accessed."
                ),
            ],
        )

    # -------------------------------------------------
    # Quantum circuit construction
    # -------------------------------------------------

    @staticmethod
    def _build_order_finding_circuit(
        n: int,
        a: int,
    ) -> QuantumCircuit:
        """
        Build the N=15 order-finding circuit.

        Registers
        ---------
        Counting register:
            4 qubits

        Work register:
            4 qubits

        Total:
            8 logical qubits

        The work register starts in |1>.

        Controlled operations implement:

            U^(2^0)
            U^(2^1)
            U^(2^2)
            U^(2^3)

        followed by the inverse QFT.
        """

        # -------------------------------------------------
        # Validate benchmark parameters
        # -------------------------------------------------

        if n != 15:
            raise ValueError(
                "Circuit currently supports N=15 only."
            )

        if a != 2:
            raise ValueError(
                "Circuit currently supports a=2 only."
            )

        # -------------------------------------------------
        # Register sizes
        # -------------------------------------------------

        counting_qubits = (
            ShorAttack.COUNTING_QUBITS
        )

        work_qubits = (
            ShorAttack.WORK_QUBITS
        )

        total_qubits = (
            counting_qubits
            + work_qubits
        )

        # -------------------------------------------------
        # Create circuit
        # -------------------------------------------------

        circuit = QuantumCircuit(
            total_qubits,
            counting_qubits,
        )

        # -------------------------------------------------
        # Step A:
        # Initialize counting register
        #
        # |0000>
        #     ↓ H⊗4
        # superposition
        # -------------------------------------------------

        for qubit in range(
            counting_qubits
        ):
            circuit.h(qubit)

        # -------------------------------------------------
        # Step B:
        # Initialize work register to |1>
        #
        # Four-bit work register:
        #
        # |0001>
        # -------------------------------------------------

        circuit.x(
            counting_qubits
        )

        # -------------------------------------------------
        # Work-register indices
        # -------------------------------------------------

        work = list(
            range(
                counting_qubits,
                total_qubits,
            )
        )

        # -------------------------------------------------
        # Step C:
        # Controlled modular exponentiation
        #
        # control = 0
        #       U^(2^0) = U
        #
        # control = 1
        #       U^(2^1) = U²
        #
        # control = 2
        #       U^(2^2) = U⁴
        #
        # control = 3
        #       U^(2^3) = U⁸
        #
        # where
        #
        # U|y> = |2y mod 15>
        # -------------------------------------------------

        for control in range(
            counting_qubits
        ):

            controlled_modular_power_2(
                qc=circuit,
                control=control,
                exponent_power=control,
                work_qubits=work,
            )

        # -------------------------------------------------
        # Step D:
        # Inverse Quantum Fourier Transform
        # -------------------------------------------------

        inverse_qft = (
            QFTGate(
                num_qubits=counting_qubits,
            ).inverse()
        )

        circuit.append(
            inverse_qft,
            range(counting_qubits),
        )

        # -------------------------------------------------
        # Step E:
        # Measurement
        # -------------------------------------------------

        circuit.measure(
            range(counting_qubits),
            range(counting_qubits),
        )

        return circuit

    # -------------------------------------------------
    # Measurement → phase
    # -------------------------------------------------

    @staticmethod
    def _extract_phases(
        counts: dict[str, int],
    ) -> list[float]:
        """
        Convert measurement bitstrings into phases.

        Results are sorted by measurement frequency
        so that the most frequently observed states
        are analyzed first.

        Example:

            '0100'
                ↓
            0.25

        because:

            0100₂ = 4
            4 / 16 = 0.25
        """

        # -------------------------------------------------
        # Sort by frequency
        # -------------------------------------------------

        ordered = sorted(
            counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        phases = []

        # -------------------------------------------------
        # Convert each state
        # -------------------------------------------------

        for bitstring, _count in ordered:

            phase = bitstring_to_phase(
                bitstring
            )

            phases.append(
                phase
            )

        return phases

