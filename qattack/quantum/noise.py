
from __future__ import annotations

from dataclasses import dataclass

from qiskit_aer.noise import (
    NoiseModel,
    ReadoutError,
    depolarizing_error,
    thermal_relaxation_error,
)


@dataclass(frozen=True)
class NoiseConfig:
    """
    Configuration for local Aer noise experiments.

    Supported models:

        ideal
        depolarizing
        readout
        thermal

    The configuration is intentionally small and
    research-benchmark oriented.
    """

    model: str = "ideal"

    depolarizing_probability: float = 0.0

    readout_probability: float = 0.0

    thermal_t1: float = 100.0
    thermal_t2: float = 80.0
    gate_time: float = 0.05

    # -------------------------------------------------
    # Normalized model name
    # -------------------------------------------------

    def normalized_model(self) -> str:
        """
        Return a normalized noise-model name.
        """

        return self.model.lower().strip()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def validate(self) -> None:
        """
        Validate noise configuration.
        """

        model = self.normalized_model()

        valid_models = {
            "ideal",
            "depolarizing",
            "readout",
            "thermal",
        }

        if model not in valid_models:
            raise ValueError(
                "Unsupported noise model: "
                f"{self.model}"
            )

        if not 0.0 <= self.depolarizing_probability <= 1.0:
            raise ValueError(
                "depolarizing_probability must be "
                "between 0 and 1."
            )

        if not 0.0 <= self.readout_probability <= 1.0:
            raise ValueError(
                "readout_probability must be "
                "between 0 and 1."
            )

        if self.thermal_t1 <= 0.0:
            raise ValueError(
                "thermal_t1 must be greater than zero."
            )

        if self.thermal_t2 <= 0.0:
            raise ValueError(
                "thermal_t2 must be greater than zero."
            )

        if self.gate_time <= 0.0:
            raise ValueError(
                "gate_time must be greater than zero."
            )


# =============================================================
# Noise model construction
# =============================================================


def build_noise_model(
    config: NoiseConfig | None = None,
) -> NoiseModel | None:
    """
    Build a Qiskit Aer NoiseModel.

    Parameters
    ----------
    config:
        Noise configuration.

        None:
            Equivalent to ideal simulation.

    Returns
    -------
    NoiseModel | None
        A configured Aer NoiseModel.

        For the ideal model, returns None.
    """

    if config is None:
        return None

    if not isinstance(config, NoiseConfig):
        raise TypeError(
            "config must be a NoiseConfig instance "
            "or None."
        )

    config.validate()

    model = config.normalized_model()

    # ---------------------------------------------------------
    # Ideal simulation
    # ---------------------------------------------------------

    if model == "ideal":
        return None

    # ---------------------------------------------------------
    # Create noise model
    # ---------------------------------------------------------

    noise_model = NoiseModel()

    # ---------------------------------------------------------
    # Depolarizing noise
    # ---------------------------------------------------------

    if model == "depolarizing":

        probability = (
            config.depolarizing_probability
        )

        one_qubit_error = depolarizing_error(
            probability,
            1,
        )

        two_qubit_error = depolarizing_error(
            probability,
            2,
        )

        # Single-qubit gates
        noise_model.add_all_qubit_quantum_error(
            one_qubit_error,
            [
                "h",
                "x",
                "sx",
            ],
        )

        # Two-qubit gates
        noise_model.add_all_qubit_quantum_error(
            two_qubit_error,
            [
                "cx",
                "cz",
            ],
        )

        return noise_model

    # ---------------------------------------------------------
    # Readout noise
    # ---------------------------------------------------------

    if model == "readout":

        probability = (
            config.readout_probability
        )

        readout_error = ReadoutError(
            [
                [
                    1.0 - probability,
                    probability,
                ],
                [
                    probability,
                    1.0 - probability,
                ],
            ]
        )

        noise_model.add_all_qubit_readout_error(
            readout_error
        )

        return noise_model

    # ---------------------------------------------------------
    # Thermal relaxation
    # ---------------------------------------------------------

    if model == "thermal":

        thermal_error = thermal_relaxation_error(
            config.thermal_t1,
            config.thermal_t2,
            config.gate_time,
        )

        noise_model.add_all_qubit_quantum_error(
            thermal_error,
            [
                "h",
                "x",
                "sx",
            ],
        )

        # -----------------------------------------------------
        # Two-qubit thermal error
        #
        # Apply independent single-qubit relaxation to
        # both qubits.
        # -----------------------------------------------------

        two_qubit_thermal_error = (
            thermal_error.tensor(
                thermal_error
            )
        )

        noise_model.add_all_qubit_quantum_error(
            two_qubit_thermal_error,
            [
                "cx",
                "cz",
            ],
        )

        return noise_model

    # ---------------------------------------------------------
    # Defensive fallback
    # ---------------------------------------------------------

    raise ValueError(
        f"Unsupported noise model: {config.model}"
    )

