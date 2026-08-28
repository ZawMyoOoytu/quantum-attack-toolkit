# Quantum Attack Toolkit

**A research-oriented framework for studying quantum attack algorithms, period finding, noise effects, and reproducible benchmarking.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.5.2-purple.svg)](https://www.ibm.com/quantum/qiskit)
[![Qiskit Aer](https://img.shields.io/badge/Qiskit%20Aer-0.17.2-purple.svg)](https://github.com/Qiskit/qiskit-aer)
[![Tests](https://img.shields.io/badge/tests-51%20passed-brightgreen.svg)](#validation)
[![License](https://img.shields.io/badge/license-research-lightgrey.svg)](#license)

---

## Overview

**Quantum Attack Toolkit** is a research and experimentation framework for investigating quantum algorithms from an attack-analysis perspective.

The project currently focuses on a controlled **Shor's algorithm N=15 benchmark**, with an emphasis on:

* quantum period finding
* modular exponentiation
* quantum phase estimation
* inverse Quantum Fourier Transform
* continued-fraction order recovery
* classical order verification
* factor derivation
* simulator noise modeling
* shot-count experiments
* noise sweeps
* statistical benchmarking
* reproducible research workflows

The current implementation is intentionally limited to a small toy integer:

$$
N = 15
$$

with

$$
a = 2
$$

where the expected multiplicative order is:

$$
r = 4
$$

and the resulting factors are:

$$
15 = 3 \times 5
$$

This repository is a **research benchmark and educational framework**, not a practical RSA key-breaking system.

---

## Research Objective

The main objective is to build a modular experimental environment for studying how quantum attack algorithms behave under different computational and noise conditions.

The framework separates the attack workflow into several layers:

```text
Target
  │
  ▼
Attack Interface
  │
  ▼
Quantum Circuit
  │
  ├── Counting Register
  │
  ├── Controlled Modular Exponentiation
  │
  └── Quantum Phase Estimation
  │
  ▼
Inverse QFT
  │
  ▼
Measurement
  │
  ▼
Phase Extraction
  │
  ▼
Continued Fractions
  │
  ▼
Candidate Order Recovery
  │
  ▼
Order Verification
  │
  ▼
Factor Derivation
  │
  ▼
Benchmark Result
```

The architecture is designed so that additional quantum attacks, noise models, and benchmark experiments can be added without redesigning the entire framework.

---

# Current Benchmark

## Shor N=15

The current benchmark implements a small-scale Shor period-finding workflow for:

| Parameter            |      Value |
| -------------------- | ---------: |
| Target               | RSA-Toy-15 |
| Integer \(N\)        |         15 |
| Base \(a\)           |          2 |
| Expected order       |          4 |
| Expected factors     |      3 × 5 |
| Counting qubits      |          4 |
| Work qubits          |          4 |
| Total logical qubits |          8 |
| Simulator            | Qiskit Aer |
| Qiskit               |      2.5.2 |
| Qiskit Aer           |     0.17.2 |

The circuit performs:

1. Hadamard initialization of the counting register.
2. Preparation of the work register in \(|1\rangle\).
3. Controlled modular powers:

```text
U^(2^0)
U^(2^1)
U^(2^2)
U^(2^3)
```

4. Inverse Quantum Fourier Transform.
5. Measurement.
6. Measurement-state to phase conversion.
7. Continued-fraction candidate generation.
8. Classical order verification.
9. Factor derivation.

---

# Baseline Result

A 1024-shot N=15 benchmark produced:

```text
Attack:               shor
Target:              RSA-Toy-15
N:                    15
a:                    2

Logical qubits:       8
Circuit depth:        1393
Gate count:           1927
Shots:                1024

Success probability:  1.0000

Recovered order:      4
Order verified:       True

Recovered factors:    (3, 5)
Expected order:       4
Expected factors:     (3, 5)
```

Representative measurement output:

```text
counts:
{
    '1100': 280,
    '0100': 261,
    '0000': 244,
    '1000': 239
}
```

Corresponding extracted phases:

```text
[0.75, 0.25, 0.0, 0.5]
```

Candidate orders:

```text
[4, 1, 2]
```

The verified order was:

```text
r = 4
```

and the derived factors were:

```text
3 × 5 = 15
```

---

# Shot-Count Benchmark

A repeated experiment was performed across four shot configurations.

Each configuration used **10 trials**.

| Shots | Trials | Successful | Success Rate | Order Recovery | Factor Recovery |
| ----: | -----: | ---------: | -----------: | -------------: | --------------: |
|   128 |     10 |         10 |         100% |           100% |            100% |
|   256 |     10 |         10 |         100% |           100% |            100% |
|   512 |     10 |         10 |         100% |           100% |            100% |
|  1024 |     10 |         10 |         100% |           100% |            100% |

Recorded mean execution times from the experiment:

| Shots | Mean elapsed time |
| ----: | ----------------: |
|   128 |          ~0.299 s |
|   256 |          ~0.298 s |
|   512 |          ~0.299 s |
|  1024 |          ~0.300 s |

The corresponding raw experiment data is stored in:

```text
results/shor_n15_shot_experiment.csv
```

---

# Noise Benchmark

The toolkit includes configurable simulator noise models.

Currently supported research configurations include:

```text
ideal
depolarizing
readout
thermal
```

The noise API is implemented in:

```text
qattack/quantum/noise.py
```

## Depolarizing Noise

A preliminary depolarizing-noise sweep was performed using:

```text
N = 15
a = 2
shots = 128
trials = 2
```

Tested probabilities:

```text
p = 0.00
p = 0.01
p = 0.02
```

Observed results:

| Depolarizing probability | Trials | Success | Order recovery | Factor recovery |
| -----------------------: | -----: | ------: | -------------: | --------------: |
|                     0.00 |      2 |    100% |           100% |            100% |
|                     0.01 |      2 |    100% |           100% |            100% |
|                     0.02 |      2 |    100% |           100% |            100% |

These results are **preliminary** and should not be interpreted as evidence that Shor's algorithm is robust against realistic quantum hardware noise.

The sample size is small, and the benchmark uses the very small N=15 problem.

---

# Noise Sweep Framework

The repository now includes a reusable depolarizing noise sweep interface:

```python
from qattack.benchmarking.noise_sweep import (
    run_depolarizing_sweep,
)

results = run_depolarizing_sweep(
    [0.0, 0.01, 0.02],
    shots=128,
    trials=5,
)
```

Each sweep reports:

* noise model
* noise probability
* number of shots
* number of trials
* successful trials
* failed trials
* success rate
* order recovery rate
* factor recovery rate

This provides the basis for larger statistical studies.

---

# Project Structure

```text
quantum-attack-toolkit/
│
├── qattack/
│   │
│   ├── analysis/
│   │   ├── factor.py
│   │   ├── order.py
│   │   └── phase.py
│   │
│   ├── attacks/
│   │   └── shor.py
│   │
│   ├── benchmarking/
│   │   ├── experiment.py
│   │   ├── export.py
│   │   ├── matrix.py
│   │   ├── metrics.py
│   │   ├── noise_sweep.py
│   │   ├── runner.py
│   │   └── statistics.py
│   │
│   ├── core/
│   │   ├── attack.py
│   │   ├── registry.py
│   │   ├── result.py
│   │   └── target.py
│   │
│   ├── quantum/
│   │   ├── modular.py
│   │   ├── noise.py
│   │   └── phase_estimation.py
│   │
│   └── reporting/
│       └── report.py
│
├── reports/
│   ├── shor_n15_benchmark.json
│   └── shor_n15_benchmark.txt
│
├── results/
│   └── shor_n15_shot_experiment.csv
│
├── tests/
│   ├── test_analysis.py
│   ├── test_benchmarking.py
│   ├── test_experiment.py
│   ├── test_export.py
│   ├── test_matrix.py
│   ├── test_modular.py
│   ├── test_order_recovery.py
│   ├── test_periodicity.py
│   ├── test_phase_estimation.py
│   ├── test_reporting.py
│   ├── test_runner.py
│   ├── test_statistics.py
│   └── test_statistics_analysis.py
│
├── pytest.ini
├── .gitignore
└── README.md
```

---

# Installation

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
pip install qiskit==2.5.2 qiskit-aer==0.17.2
```

Install testing dependencies if required:

```powershell
pip install pytest
```

---

# Running the Benchmark

Run the basic N=15 Shor benchmark:

```powershell
python -c "from qattack.attacks.shor import ShorAttack; from qattack.core.target import Target; a=ShorAttack(); t=Target(target_type='rsa', name='RSA-Toy-15', size=15); r=a.run(t, shots=1024); print(r.summary())"
```

A successful result should recover:

```text
order = 4
factors = (3, 5)
```

---

# Running the Shot Experiment

Run the benchmark matrix:

```powershell
python -c "from qattack.benchmarking.experiment import run_experiment_matrix; r=run_experiment_matrix('shor-n15',[128,256,512,1024],trials=10); [print(x.summary()) for x in r]"
```

---

# Running the Noise Sweep

Run:

```powershell
python -c "from qattack.benchmarking.noise_sweep import run_depolarizing_sweep; r=run_depolarizing_sweep([0.0,0.01,0.02],shots=128,trials=5); [print(x.summary()) for x in r]"
```

---

# Running Tests

The project currently contains a test suite covering the core analysis, quantum components, benchmarking, statistics, and reporting layers.

Run:

```powershell
pytest -q
```

Current validation:

```text
51 passed
```

The latest recorded test execution completed successfully:

```text
51 passed in 17.55s
```

---

# Reproducibility

The repository is designed around reproducible local simulation.

The benchmark records:

* attack type
* target
* problem size
* shot count
* trial count
* success rate
* order recovery rate
* factor recovery rate
* execution time
* logical qubit count
* circuit depth
* gate count
* measurement counts
* extracted phases
* candidate orders
* recovered order
* recovered factors
* noise configuration

Benchmark artifacts are stored under:

```text
reports/
results/
```

This allows experimental outputs to be inspected independently of the execution code.

---

# Research Interpretation

The current results demonstrate that the implemented N=15 benchmark can successfully execute the complete period-finding workflow under local simulation.

However, several important distinctions must be maintained.

### What the benchmark demonstrates

The implementation demonstrates:

* construction of a small Shor-style order-finding circuit
* controlled modular exponentiation
* phase estimation
* inverse QFT
* measurement processing
* continued-fraction candidate generation
* classical order verification
* factor derivation
* reproducible simulation experiments
* configurable noise experiments

### What the benchmark does NOT demonstrate

It does **not** demonstrate:

* breaking production RSA
* recovering real cryptographic keys
* attacking a third-party system
* practical cryptanalysis of RSA-2048
* fault-tolerant quantum computation
* hardware-scale Shor performance
* realistic cryptographic security estimates

The N=15 problem is deliberately tiny and is used as a controlled research benchmark.

---

# Security and Ethical Scope

This project is intended for:

* quantum computing research
* cryptography research
* post-quantum security analysis
* algorithm benchmarking
* educational experimentation
* simulator-based quantum security studies

The current implementation operates on a toy mathematical target and does not access credentials, private keys, external systems, or third-party infrastructure.

---

# Research Roadmap

## Phase 1 — Core Shor Benchmark

* [x] N=15 benchmark
* [x] Modular arithmetic
* [x] Controlled modular powers
* [x] Phase estimation
* [x] Inverse QFT
* [x] Order recovery
* [x] Factor derivation
* [x] Result reporting

## Phase 2 — Benchmarking

* [x] Shot-count experiments
* [x] Repeated trials
* [x] Benchmark statistics
* [x] CSV export
* [x] JSON reporting
* [x] Text reporting

## Phase 3 — Noise Research

* [x] Ideal simulator
* [x] Depolarizing noise
* [x] Readout noise
* [x] Thermal relaxation model
* [x] Depolarizing noise sweep
* [ ] Larger noise sweep
* [ ] Confidence intervals
* [ ] Failure-mode classification
* [ ] Noise-vs-recovery plots

## Phase 4 — Hardware-Aware Benchmarking

Planned research directions include:

* [ ] hardware calibration data
* [ ] realistic gate-error parameters
* [ ] backend-aware transpilation
* [ ] hardware topology analysis
* [ ] circuit-depth sensitivity
* [ ] measurement-error analysis
* [ ] error mitigation experiments

## Phase 5 — Scalable Research Framework

Future work may investigate:

* [ ] larger composite integers
* [ ] additional order-finding configurations
* [ ] alternative modular arithmetic implementations
* [ ] resource estimation
* [ ] circuit scaling analysis
* [ ] quantum resource benchmarking
* [ ] comparative classical/quantum analysis

---

# Research Questions

The framework is intended to support questions such as:

1. How does measurement-shot count affect successful order recovery?

2. How does depolarizing noise affect phase estimation?

3. At what noise levels does candidate-order recovery become unreliable?

4. How does circuit depth correlate with factor-recovery failure?

5. Which stages of the Shor workflow are most sensitive to noise?

6. How does transpilation affect the resource requirements of modular exponentiation?

7. How does simulator behavior compare with real quantum hardware?

8. What resource scaling is required when moving beyond toy integer sizes?

---

# Limitations

The current implementation has several limitations:

* Only N=15 is currently supported by the Shor benchmark.
* The implementation uses a simplified modular arithmetic construction.
* Results are simulator-based.
* The current noise experiments use configurable synthetic noise models.
* The preliminary noise sweep uses a small number of trials.
* The benchmark does not represent fault-tolerant quantum computation.
* The reported execution time is environment-dependent.
* The current success metric represents successful recovery within the benchmark pipeline, not cryptographic attack feasibility.

These limitations are intentionally documented to prevent overinterpretation of the experimental results.

---

# Citation

If this repository contributes to academic research, please cite the repository and the associated research work when available.

```text
ZawMyo Oo,
"Quantum Attack Toolkit: A Research Framework for Quantum Attack
Algorithms and Reproducible Benchmarking,"
GitHub, 2026.
```

Repository:

```text
https://github.com/ZawMyoOoytu/quantum-attack-toolkit
```

---

# License

This repository is currently intended as a research and educational project.

License terms should be added explicitly before using the repository as a production or commercial dependency.

---

# Status

**Research Prototype — Active Development**

Current validated state:

```text
Shor N=15 benchmark       ✓
Quantum period finding    ✓
Order recovery            ✓
Factor recovery           ✓
Shot benchmark            ✓
Noise models              ✓
Noise sweep               ✓
Automated tests           ✓

Tests                     51 passed
Logical qubits            8
Baseline circuit depth    1393
Baseline gate count       1927
```

The project is being developed toward a broader experimental framework for **quantum attack benchmarking, noise-aware analysis, and quantum cryptographic security research**.
