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
