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

## Objectives

1. Establish a precise entry point: determine what the existing literature has
   proven and implemented, what it has not, and the concrete step from which
   this project proceeds.
2. Build a reproducible experimental platform: benchmark instances, an
   evaluation protocol and a runnable harness producing comparable results.
3. Design steady-state EA variants for permutation problems with controllable
   selective pressure.
4. Evaluate them against existing algorithms under a common protocol and
   report the resulting evidence.

## Methodology

The project follows the steady-state EA framework and its measure of selective
pressure established for Pseudo-Boolean optimisation, and extends it to
permutation encodings. Work combines theoretical reasoning with controlled
experiments: selection and variation operators are chosen to expose the
exploration/exploitation trade-off, and performance is measured by the gap to
known optima under fixed evaluation budgets, with statistical comparison across
independent runs.

## Phase 1: Entry Point and Test Platform

Phase 1 spans the first week and addresses Objectives 1 and 2.

**Task 1 - Find the entry point.** Reconstruct the steady-state model and its
notation, separate what is proven from what is observed or conjectured, examine
the dependence of each result on the Pseudo-Boolean representation, and survey
the permutation-side literature. The output is a concise entry-point note
stating the research gap and a concrete first experiment.

**Task 2 - Build the test platform.** Select benchmark instances (TSPLIB;
QAPLIB and random uniform instances if a broader claim is required), define an
evaluation standard (gap to optimum, fixed budget, independent runs,
significance testing) and implement a seeded, reproducible harness with a
machine-readable result format.

The detailed schedule, tasks and deliverables are given in the project plan
document.

## Repository Layout

```
docs/     Project plan and report sources (Typst)
output/   Compiled PDFs (generated, not tracked)
justfile  Build recipes
```

## Building

The documents are written in [Typst](https://typst.app/) and built with
[just](https://github.com/casey/just).

```sh
just compile   # compile every docs/*.typ into output/
just clean     # remove generated output
```

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
