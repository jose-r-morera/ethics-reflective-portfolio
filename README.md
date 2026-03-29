# CitySwift: Ethical and Functional Transit Optimization Engine

## Authors
*   **Pelayo García Álvarez**
*   **José Ramón Morera Campos**

---

## Project Overview
This repository contains the technical implementation and reflective portfolio of the **CitySwift Performance Optimisation Platform**, developed for the MSc in Advanced Artificial Intelligence at University College Dublin (UCD). 

The system focuses on utilizing a neuro-symbolic AI architecture to enforce formal ethical constraints over a functional transit optimization model, using the **Z3 Theorem Prover** for validation.

## Technical Framework
The system is modeled as a Constraint Satisfaction Problem (CSP) where operational utility is maximized subject to physical, legal, and normative ethical invariants.

### Ethical Normative Constraints
*   **E1: Minimum Service Floor** – Ensures critical infrastructure (e.g., medical and educational facilities) maintains at least **80%** of baseline frequency.
*   **E2: Distributive Justice** – Prevents the emergence of "transit deserts" by guaranteeing a 60% minimum coverage across all urban zones.
*   **E3: Operator Fairness** – Requires a 95% confidence threshold for automated delay penalties and punitive classifications.
*   **E4: Virtue of Care** – Prioritizes passenger safety over carbon efficiency during extreme weather conditions.
*   **E5: Fatigue Mitigation** – Implements a 10% safety buffer for driver workload to prevent cognitive exhaustion.
*   **E6: GDPR Privacy** – Enforces anonymization and consent-based protocols for passenger telemetry.

### Functional Objectives
*   **F1: Network Utility Maximization** – Utilization of a saturation model for passenger throughput.
*   **F2: Resource Constraint Satisfaction** – Adherence to fleet size and total driver-hour capacity.
*   **F3: Predictable Synchronization** – Maintenance of scheduled headways within a +/- 15-minute deviation.

## Usage and Requirements
### Prerequisites
*   Python 3.x
*   Z3 Theorem Prover (`pip install z3-solver`)

### Execution
Run the main validation engine to simulate standard operational scenarios and failure-state detections:
```bash
python3 cityswift_z3_implementation.py
```

