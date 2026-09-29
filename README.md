# Steady-State Evolutionary Algorithms for Permutation-Based Combinatorial Optimisation

A research project on the design and empirical evaluation of steady-state
Evolutionary Algorithms (EAs) for permutation problems, with the Travelling
Salesman Problem (TSP) as the primary case study.

## Overview

Evolutionary Algorithms are commonly organised under two population models.
In the *generational* model the entire population is replaced each generation,
whereas in the *steady-state* model only a subset of the population is
replaced per generation. Recent theoretical and experimental work on
Pseudo-Boolean optimisation has shown that the steady-state model permits
tighter control of the exploration/exploitation balance, achieved through
counter-intuitive selection operators, in particular an inverse rank-based
allocation of reproductive trials.

It remains unclear whether these results transfer to permutation-based
combinatorial optimisation, where the search space, the neighbourhood
structure and the variation operators differ substantially from the
Pseudo-Boolean setting. This project investigates that question: it designs
steady-state EAs with controlled selective pressure for permutation problems
and compares their performance against established algorithms.

## Motivation

Permutation problems such as the TSP are canonical NP-hard combinatorial
optimisation problems with well-established benchmark suites and known optimal
solutions. They therefore provide both a demanding test bed and a fair basis
for comparison. If the Pseudo-Boolean findings on selective pressure carry over,
they would offer a principled mechanism for tuning evolutionary search on a
broad class of problems; if they do not, characterising the failure would
itself clarify the boundary of the existing theory.

## Repository Layout

```
benchmarks/             Development instances and benchmark metadata
configs/                Version-controlled experiment specifications
docs/                   Project plan and report sources (Typst)
src/tsp_perm_ea_bench/  Python problem, algorithm, and logging packages
tests/                  Correctness and reproducibility tests
output/                 Compiled PDFs (generated, not tracked)
results/                Experiment artifacts (generated, not tracked)
justfile                Build recipes
```

## Building

The documents are written in [Typst](https://typst.app/) and built with
[just](https://github.com/casey/just).

```sh
just compile   # compile every docs/*.typ into output/
just clean     # remove generated output
```

The experiment package has no runtime dependencies beyond Python 3.11. Run
the platform checks from the repository root with:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

The first executable loop is a single controlled run. It writes a complete run
directory and an atomic completion marker:

```sh
PYTHONPATH=src python -m tsp_perm_ea_bench.cli.main run \
  --instance benchmarks/instances/square.tsp \
  --instance-id square \
  --output-directory results/smoke/runs \
  --seed 1000 \
  --repeat 0 \
  --population-size 20 \
  --offspring-budget 100
```

The formal five-instance suite is not frozen yet. The checked-in benchmark
fixtures are development-only correctness inputs and must not be presented as
the formal study data.

Useful development commands are available through `just`:

```sh
just test
just validate-benchmarks
just smoke-plan
PYTHONPATH=src python -m tsp_perm_ea_bench.cli.main batch \
  --config configs/development-smoke.json
```

The batch runner records each task under a stable run identity, keeps failed
attempts, and skips a run only after its completion marker and summary have
both passed integrity checks. `summarize` rebuilds CSV tables and a standard
library SVG from completed artifacts; failed attempts are listed separately.

## References

1. D. Corus, A. Lissovoi, P. S. Oliveto, and C. Witt, "On steady-state
   evolutionary algorithms and selective pressure: Why inverse rank-based
   allocation of reproductive trials is best," *ACM Transactions on
   Evolutionary Learning and Optimization*, vol. 1, no. 1, 2021.
   doi: 10.1145/3427474.
2. J. Gottlieb and T. Kruse, "Selection in evolutionary algorithms for the
   traveling salesman problem," in *Proceedings of the 2000 ACM Symposium on
   Applied Computing (SAC '00)*, vol. 1, New York, NY, USA, 2000, pp. 415-421.
   doi: 10.1145/335603.335869.
