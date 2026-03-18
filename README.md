# RLFA Optimization Engine

A high-performance Constraint Satisfaction Problem (CSP) solver built in Python, designed to resolve the **Radio Link Frequency Assignment Problem (RLFAP)**.

## 📡 The Problem
Originally sourced from the French Centre d'Electronique de l'Armement (CELAR), the RLFAP is a classic NP-hard telecommunications problem. The objective is to assign specific frequencies to a vast network of radio communication links. 

The solver must guarantee that no two frequencies interfere with one another (satisfying distance and equality constraints) while minimizing the total number of distinct frequencies used across the network. 

## ⚙️ Core Architecture
This engine is built for raw algorithmic efficiency, stripping away standard textbook boilerplate in favor of optimized data structures.

* **Constraint Engine:** Utilizes `O(1)` dictionary lookups for constraint validation, eliminating inner-loop sorting bottlenecks during deep tree searches.
* **Inference Strategies:** * **Forward Checking (FC):** A lightweight look-ahead algorithm to prune immediate domain violations.
* **Maintaining Arc Consistency (MAC / AC-3):** A deep-pruning algorithm utilizing `collections.deque` for `O(1)` edge evaluations, drastically reducing the search space in highly constrained networks.
* **Dynamic Heuristics:** Employs the **dom/wdeg** (Domain over Weighted Degree) dynamic variable ordering heuristic. The engine dynamically learns from constraint failures (domain wipeouts), increasing the weight of difficult constraints to route the search tree away from high-conflict variables.

## 📂 Data Structure
The engine includes a custom parsing class designed to read standard RLFAP `.txt` matrices. The data is expected to be split across three files per instance:
* `varX.txt`: Variable definitions.
* `domX.txt`: Frequency domain arrays.
* `ctrX.txt`: The network interference constraints (>, =, <=).

## 🗄️ Available Instances
The `data/rlfap` directory contains the raw CELAR instances. You can pass these IDs directly into the CLI. 

* **Available IDs:** `2-f24`, `2-f25`, `3-f10`, `3-f11`, `6-w2`, `7-w1-f4`, `7-w1-f5`, `8-f10`, `8-f11`, `11`, `14-f27`, `14-f28`
* *(Note: Execution time scales non-linearly with constraint density. Instance 11 is recommended for standard benchmarking).*

## 🚀 Execution Instructions

### Prerequisites
* Python 3.8+
* A native Linux environment (or WSL) is highly recommended for accurate CPU-cycle profiling. No external dependencies or `pip` installs are required.

### Command Line Interface (CLI)
The engine is operated entirely via the terminal. 

**View the Help Menu:**
```bash
python3 rlfa_solver.py -h

# Run the default benchmark (Instance 11)
python3 rlfa_solver.py

# Run a custom target (e.g., Instance 8-f10)
python3 rlfa_solver.py -i 8-f10
