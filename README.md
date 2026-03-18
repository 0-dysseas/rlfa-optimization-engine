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
