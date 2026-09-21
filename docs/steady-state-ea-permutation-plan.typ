// --- Steady-state EA for permutation problems: project plan ---
// Project description and references, written from the given project details.

#let course = "Evolutionary Computation"
#let project-title = "Evolutionary Algorithm Design for Permutation-Based Combinatorial Optimisation Problems"
#let student-id = "12410303"
#let date = "September 18, 2026"

#set page(
  paper: "us-letter",
  margin: (top: 2.4cm, bottom: 2.2cm, x: 2.5cm),
  header: [
    #set text(size: 9pt, fill: luma(90))
    #grid(
      columns: (1fr, auto, auto),
      column-gutter: 1em,
      align: (left, center, right),
      [SUSTech #course],
      [Student ID: #student-id],
      [#date],
    )
    #v(-0.6em)
    #line(length: 100%, stroke: 0.4pt + luma(180))
  ],
  footer: context {
    let page-num = counter(page).get().first()
    set align(center)
    set text(size: 9pt, fill: luma(90))
    [Page #page-num]
  },
)

#set text(font: "New Computer Modern", size: 11pt)
#set par(justify: true)
#show heading.where(level: 1): it => [
  #v(0.6em)
  #it
  #v(0.2em)
]

// --- Title block ---
#align(center)[
  #v(1em)
  #text(size: 18pt, weight: "bold")[#project-title]
  #v(1.2em)
]

#v(0.8em)

// --- Body ---

= Project Description

Two different Evolutionary Algorithm (EA) models are commonly used: the
generational model, where all individuals are replaced in each generation (i.e.,
a non-elitist model), and the steady-state model, where only a subset of the
population is replaced at every generation (i.e., an elitist model).

Recently, it has been shown theoretically and experimentally that the
steady-state model allows the balance between exploitation and exploration of
the evolutionary process to be controlled better than the generational model for
Pseudo-Boolean Optimisation. This is achieved by using counter-intuitive
selection operators, which yet lead to surprising performance.

However, it is unclear whether the results carry over to permutation-based
combinatorial optimisation problems such as the travelling salesman problem. In
this project, steady-state EAs with good exploration/exploitation capabilities
for permutation problems will be designed and their performance compared against
existing algorithms. A high-quality project may lead to a published research
paper.

= Phase 1: Entry Point and Test Platform

Phase 1 spans the first week. It has two goals: (i) pin down the exact
research gap left by the existing literature and the point at which this
project starts, and (ii) stand up the experimental platform needed to
measure progress in later phases.

== Objective

- Produce a precise, written statement of the *entry point*: what the
  previous work has already established, what it has not, and which concrete
  step this project takes first.
- Produce a reproducible *test platform*: a set of benchmark instances, an
  evaluation protocol, and a runnable harness that reports comparable
  numbers.

== Task 1: Find the entry point

The baseline is the steady-state EA theory of Corus et al. [1], which shows
that in the steady-state model the exploration/exploitation balance can be
controlled through the allocation of reproductive trials, and that an
inverse rank-based allocation is best. These results are proven for
Pseudo-Boolean optimisation (e.g., OneMax, LeadingOnes) and are not
obviously transferable to permutation spaces.

Planned actions:

- Reconstruct the steady-state model and its notation from [1]: population
  size, replacement rule, selection and variation operators, and the
  measure of selective pressure.
- Separate what is *proven*, what is *observed experimentally*, and what is
  *conjectured* in [1].
- Check each result's dependence on the Pseudo-Boolean representation
  (bit-flip mutation, hypercube structure) and decide which parts survive a
  permutation encoding (swap / insertion / inversion mutation, crossover).
- Survey the follow-up literature and the permutation side (e.g., [2] and
  successor work) for any existing steady-state or rank-based allocation
  results, to avoid re-deriving known facts.
- State the gap explicitly: which steady-state selection operators, if any,
  have been analysed or benchmarked on permutation problems, and where the
  simplest defensible starting point lies.

Expected output: a 1--2 page entry-point note with a single concrete first
experiment proposal (representation, operator set, population size,
replacement scheme, target problem class).

== Task 2: Build the test platform

This breaks into (a) benchmark instances, (b) an evaluation standard, and
(c) a harness.

Benchmark instances (to be confirmed against the literature):

- *Travelling salesman*: the TSPLIB symmetric instances, using a small
  subset (e.g., eil51, kroA100, pr1002, pcb442) with known optimal tours so
  that solution quality can be normalised.
- *Other permutation problems*, if needed for a broader claim: QAPLIB for
  the quadratic assignment problem, and/or random uniform instances (one
  and two dimensional) for controllability.
- Record instance size, known optimum/best-known value, and provenance for
  every selected instance.

Evaluation standard:

- Report the gap to the known optimum (or best-known) per instance, not raw
  fitness.
- Fix a budget convention (number of evaluations or generations) and a
  number of independent runs per instance.
- Predefine the comparison statistics (mean/median, spread, and a
  significance test such as Wilcoxon rank-sum) and the plots to produce.

Harness:

- A single entry point that runs one configuration on one instance for a
  given seed and writes a machine-readable result record (instance, config,
  seed, budget, best found, evaluations used).
- A driver that sweeps configurations/seeds and aggregates into tables.
- A smoke test on one tiny instance to verify determinism given a seed.

Expected output: a repository skeleton with instance files, a documented
protocol, and one working end-to-end run whose raw logs are reproducible.

== Schedule

#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: (x: 0.4em, y: 0.35em),
  align: (left, left),
  [*Day*], [*Focus*],
  [1], [Read and annotate [1]; extract model, theorem statements, open questions.],
  [2], [Survey follow-up and permutation-side literature; draft the entry-point note.],
  [3], [Finalise the gap statement and the first experiment proposal; collect benchmark instances.],
  [4], [Write the evaluation protocol (budget, runs, statistics); start the harness.],
  [5], [Finish the harness; run the smoke test on one small instance.],
  [6], [Reproduce one baseline configuration end-to-end; verify logs are reproducible.],
  [7], [Review gaps in coverage; write the Phase 1 report and hand over to Phase 2.],
)

== Deliverables

- Entry-point note (1--2 pages) with the explicit gap and first experiment.
- Benchmark instance set with provenance and known optima/best-known values.
- Documented evaluation protocol.
- Working, seeded, reproducible harness with one baseline result.

= References

#set text(size: 10pt)
#enum(
  numbering: "[1]",
  [D. Corus, A. Lissovoi, P. S. Oliveto, and C. Witt, "On steady-state evolutionary
   algorithms and selective pressure: Why inverse rank-based allocation of
   reproductive trials is best," _ACM Transactions on Evolutionary Learning and
   Optimization_, vol. 1, no. 1, 2021. doi: 10.1145/3427474.],
  [J. Gottlieb and T. Kruse, "Selection in evolutionary algorithms for the traveling
   salesman problem," in _Proceedings of the 2000 ACM Symposium on Applied Computing
   (SAC '00)_, vol. 1, New York, NY, USA, 2000, pp. 415--421.
   doi: 10.1145/335603.335869.],
)
