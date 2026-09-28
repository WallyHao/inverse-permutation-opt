// --- Crossover algorithm selection for permutation-based steady-state GAs ---

#let course = "Evolutionary Computation"
#let project-title = "Crossover Algorithm Selection for Permutation-Based Steady-State GAs"
#let date = "September 28, 2026"

#set page(
  paper: "us-letter",
  margin: (top: 2.4cm, bottom: 2.2cm, x: 2.5cm),
  header: [
    #set text(size: 9pt, fill: luma(90))
    #grid(
      columns: (1fr, auto),
      column-gutter: 1em,
      align: (left, right),
      [SUSTech #course],
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

#align(center)[
  #v(1em)
  #text(size: 18pt, weight: "bold")[#project-title]
  #v(1.2em)
]


= 1. Research objective

This document locks the crossover direction for the permutation-optimisation project. The primary problem is the symmetric Traveling Salesman Problem (TSP), represented directly as a permutation of city IDs. The experimental question is:

#quote(block: true)[
How do crossover operators that preserve different permutation features—position, relative order, and adjacency—affect the performance and diversity of a steady-state genetic algorithm on permutation optimisation problems?
]

The goal is not to implement every known permutation crossover. The goal is to compare a small set of operators whose preservation behaviour is meaningfully different, then test one project-specific adaptive method built from that comparison.

The selected experimental set is:

1. *PMX — Partially Mapped Crossover*: position/mapping-oriented baseline.
2. *OX — Order Crossover*: relative-order baseline and main conventional baseline.
3. *ERX — Edge Recombination Crossover*: adjacency/edge-preserving comparison.
4. *SAX — Structure-Adaptive Crossover (project method)*: dynamically chooses OX or ERX from parent edge diversity.

This set is intentionally small. PMX, OX, and ERX represent three different preservation philosophies. SAX tests whether information about the current parent pair can be used to select the better preservation behaviour instead of fixing one crossover for the whole run.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 2. Current project understanding

The public repository currently defines a research project on *steady-state evolutionary algorithms for permutation-based combinatorial optimisation*, with TSP as the main case study. Its stated motivation is to test whether findings about controlled and inverse selective pressure from pseudo-Boolean optimisation transfer to permutation search spaces.

The current public repository is documentation-first. The visible root contains `docs/`, `.gitignore`, `README.md`, and `justfile`; there is no visible GA implementation directory in the public tree at the time of this analysis. The `justfile` compiles Typst files from `docs/` into `output/`.

The related thesis material uses a steady-state `(μ + 1)` GA for TSP with permutation tours, crossover, single-city displacement mutation, optional 2-opt local search, and elitist replacement. It also shows that parent-selection policy strongly interacts with crossover: using the same low-pressure selection for both parents can make crossover degenerate, while selecting the first parent by the target operator and the second parent uniformly at random (RPS) can reveal the benefit of low selective pressure.

For the crossover study, the GA structure should therefore stay fixed and crossover should be the main changing factor.

=== Representation

A tour is represented directly as a permutation:

```text
[1, 5, 3, 2, 4]
```

For a symmetric TSP this represents the cyclic tour:

```text
1 -> 5 -> 3 -> 2 -> 4 -> 1
```

Every crossover must return a valid permutation containing every city exactly once.

=== Reusable project ideas

Even though no public implementation is visible yet, the existing research design can be reused:

- steady-state `(μ + 1)` population model;
- permutation path representation;
- TSP distance-matrix fitness evaluation;
- low/sub-uniform parent selection for Parent 1;
- random Parent 2 policy (RPS);
- single-city displacement mutation;
- elitist replacement;
- optimality-gap and edge-diversity metrics;
- TSPLIB instances with known optima.

The crossover implementation should plug into this structure rather than redesigning the GA.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 3. Why an inverse-permutation crossover is not selected

The repository name contains `inverse-permutation-opt`, but the public research description uses *inverse selection pressure / inverse rank-based reproductive allocation* as the motivating idea. It does not establish inverse permutations as the solution representation.

For a direct permutation `P`, the inverse permutation `Q` is:

```text
P[position] = value
Q[value]    = position
```

Example:

```text
P = [4, 1, 3, 2]
Q = [2, 4, 3, 1]   // using 1-based positions
```

A tempting idea is to convert both parents to inverse permutations, run OX/PMX there, and invert the result back. This is *not selected as a main method* for three reasons:

1. A contiguous crossover interval in inverse space is indexed by city labels. TSP city labels are arbitrary identifiers, so preserving a block of consecutive labels has no natural geometric or tour meaning.
2. A subset-based version of this idea largely reduces to known position-based crossover behaviour: it fixes selected cities to inherited positions and fills the rest from the other parent.
3. The project's core scientific question is better served by explicitly contrasting position, order, and adjacency preservation rather than adding a representation transform whose preserved feature is difficult to interpret for TSP.

If later work uses a problem where element identity has an ordered semantic meaning, inverse-space crossover may become more justified. It should not be forced into the initial TSP experiment.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 4. Final selected algorithms

== 4.1 PMX — Partially Mapped Crossover

=== Role in the experiment

PMX is the *position/mapping-oriented baseline*. It tests whether preserving a copied positional segment plus a value mapping is useful under the same steady-state GA.

=== What PMX preserves

PMX preserves:

- the exact positions of the copied segment from one parent;
- a mapping relationship induced by the two parent segments;
- some positional information from the other parent after conflicts are repaired.

It does *not* explicitly preserve TSP adjacency.

=== Why that matters

PMX is useful because TSP fitness is edge-based, not position-based. If PMX underperforms ERX while showing higher positional preservation, that is evidence that preserving the wrong feature can reduce search effectiveness even when offspring are valid permutations.

=== Worked example

Use the same parents for all examples:

```text
Parent 1 = [1, 2, 3, 4, 5, 6, 7, 8]
Parent 2 = [4, 1, 2, 8, 7, 6, 5, 3]
```

Use crossover positions 3..5 (1-based):

```text
P1 = [1, 2 | 3, 4, 5 | 6, 7, 8]
P2 = [4, 1 | 2, 8, 7 | 6, 5, 3]
```

Copy P1's middle segment into Child 1:

```text
Child 1 = [_, _, 3, 4, 5, _, _, _]
```

The segment mapping is:

```text
3 <-> 2
4 <-> 8
5 <-> 7
```

Fill outside positions from Parent 2:

- position 1 proposes `4`; `4` is already in the copied segment. Follow the mapping `4 -> 8`, so write `8`.
- position 2 proposes `1`; it is unused, so write `1`.
- position 6 proposes `6`; unused, so write `6`.
- position 7 proposes `5`; conflict. Follow `5 -> 7`, so write `7`.
- position 8 proposes `3`; conflict. Follow `3 -> 2`, so write `2`.

Final Child 1:

```text
[8, 1, 3, 4, 5, 6, 7, 2]
```

For Child 2, copy Parent 2's segment and repair Parent 1's conflicting values:

```text
Child 2 = [1, 3, 2, 8, 7, 6, 5, 4]
```

Both children are valid permutations.

=== Pros

- *Clear positional baseline.* It gives the study a crossover whose main inherited structure is different from OX and ERX, so differences in performance are scientifically interpretable.
- *Validity by construction.* Mapping-based conflict repair guarantees each city occurs exactly once.
- *Controlled disruption.* A contiguous block survives exactly, while the rest can change. This provides a moderate exploration/exploitation balance.
- *General permutation applicability.* PMX is not tied specifically to TSP edges, so it is a useful reference when later testing scheduling or assignment permutations.

=== Cons

- *Feature mismatch for TSP.* Absolute positions have limited meaning in a cyclic tour. Rotating the same tour changes every position without changing the route cost.
- *Can destroy good edges.* The mapping repair may place cities in valid but poor adjacencies.
- *Representation sensitivity.* Equivalent cyclic tours with different starting points can appear positionally very different.
- *Conflict logic is more complex than OX.* Mapping chains must be implemented carefully to avoid duplicates or loops.

=== Implementation plan

Main data structures:

- output arrays of length `n` initialised with a sentinel such as `-1`;
- `Map<number, number>` for segment mappings;
- `Set<number>` or boolean-index table for membership in the copied segment.

Expected complexity:

- time: `O(n)` average with `Map`/`Set`;
- space: `O(n)`.

Validity guarantee: if both parents contain the same unique value set, PMX outputs the same value set exactly once.

Important tests:

- known worked example above;
- random property test: result sorted equals parent sorted;
- cut range of one element;
- cut range covering all elements;
- parents identical;
- parents reversed;
- deterministic output with seeded RNG.

#line(length: 100%, stroke: 0.4pt + luma(180))

== 4.2 OX — Order Crossover

=== Role in the experiment

OX is the *main conventional baseline* and the relative-order operator.

=== What OX preserves

OX preserves:

- one exact contiguous segment from Parent 1;
- the relative encounter order of remaining values from Parent 2.

This makes it fundamentally different from PMX's mapping/position behaviour and ERX's adjacency behaviour.

=== Why that matters

Many permutation problems encode useful information in relative order. OX therefore provides the cleanest order-preserving comparison. On TSP it can also inherit several edges inside the copied segment, but it does not explicitly optimise edge inheritance.

=== Worked example

Parents:

```text
Parent 1 = [1, 2, 3, 4, 5, 6, 7, 8]
Parent 2 = [4, 1, 2, 8, 7, 6, 5, 3]
```

Use positions 3..5:

```text
P1 = [1, 2 | 3, 4, 5 | 6, 7, 8]
```

Copy the segment into Child 1:

```text
Child 1 = [_, _, 3, 4, 5, _, _, _]
```

Scan Parent 2 starting immediately after the second cut, wrapping to the front:

```text
scan order = [6, 5, 3, 4, 1, 2, 8, 7]
```

Remove values already present in Child 1 (`3, 4, 5`):

```text
remaining = [6, 1, 2, 8, 7]
```

Fill the empty child positions starting after the second cut and wrapping:

```text
positions = [6, 7, 8, 1, 2]
values    = [6, 1, 2, 8, 7]
```

Final Child 1:

```text
[8, 7, 3, 4, 5, 6, 1, 2]
```

Repeating symmetrically gives:

```text
Child 2 = [4, 5, 2, 8, 7, 6, 1, 3]
```

=== Pros

- *Directly tests relative-order preservation.* This is a distinct feature class from PMX and ERX.
- *Validity is straightforward.* Values already in the copied segment are skipped when filling.
- *Low implementation risk.* The algorithm is simple enough that crossover behaviour is unlikely to be hidden by repair bugs.
- *Strong general baseline.* It is relevant to TSP and to many sequence/order-based permutation problems.
- *Useful diversity behaviour.* It can produce children with substantially different positions while preserving meaningful order information.

=== Cons

- *Does not explicitly protect good TSP edges.* Edges outside the copied segment can be broken even when both parents contain useful adjacency information.
- *Cyclic wrap-around affects semantics.* The chosen linear representation imposes a start point on a cyclic TSP tour.
- *Can become conservative when parents are already similar.* If parents have nearly the same ordering, OX produces little new structure.

=== Implementation plan

Data structures:

- child array length `n`, initialised to `-1`;
- `Set<number>` of copied values;
- two integer cut indices;
- circular scan helper.

Expected complexity:

- time: `O(n)`;
- space: `O(n)`.

Useful helper:

```text
fillOrder(child, donor, usedValues, startIndex)
```

Important tests:

- worked example;
- permutation property over hundreds of seeded random parent pairs;
- segment size 1;
- full segment;
- wrap-around filling;
- identical parents;
- deterministic cut-point injection for exact unit tests.

#line(length: 100%, stroke: 0.4pt + luma(180))

== 4.3 ERX — Edge Recombination Crossover

=== Role in the experiment

ERX is the *adjacency-preserving operator*. It is the most TSP-aligned of the conventional selected methods.

=== What ERX preserves

ERX builds a child using adjacency information from both parents. For every city, it records neighbouring cities in both parent tours. Shared edges can be marked and preferred.

=== Why that matters

For symmetric TSP, objective value is directly determined by edges:

```text
length = d(tour[0], tour[1]) + ... + d(tour[n-1], tour[0])
```

Preserving parental edges is therefore much closer to preserving actual TSP building blocks than preserving absolute positions.

=== Worked example

Parents:

```text
Parent 1 = [1, 2, 3, 4, 5, 6, 7, 8]
Parent 2 = [4, 1, 2, 8, 7, 6, 5, 3]
```

Because tours are cyclic, city `1` has neighbours `8` and `2` in Parent 1, and `4` and `2` in Parent 2.

Combined neighbour table:

```text
1 -> {2*, 4, 8}
2 -> {1*, 3, 8}
3 -> {2, 4*, 5}
4 -> {1, 3*, 5}
5 -> {3, 4, 6*}
6 -> {5*, 7*}
7 -> {6*, 8*}
8 -> {1, 2, 7*}
```

`*` means the edge occurs in both parents.

Use this deterministic demonstration policy:

1. prefer an unused shared neighbour;
2. otherwise choose the unused neighbour with the smallest remaining adjacency list;
3. break ties deterministically for the example (production code uses the seeded RNG);
4. if no parental neighbour remains, choose an unused city by RNG.

Starting from city `1`, one valid sequence is:

```text
1 -> 2 -> 8 -> 7 -> 6 -> 5 -> 3 -> 4
```

Final child:

```text
[1, 2, 8, 7, 6, 5, 3, 4]
```

This child retains many edges from the two parents, including several edges shared by both.

A second child can be generated by changing the start city and/or seeded tie decisions.

=== Pros

- *Direct feature match to TSP fitness.* It preserves the structure that actually determines tour length.
- *Natural comparison against OX/PMX.* If ERX wins while edge preservation is measurably higher, the result supports the edge-building-block hypothesis.
- *Uses both parents symmetrically.* The edge table integrates adjacency information from both tours instead of privileging only one fixed segment.
- *Still permutation-valid.* Each city is appended once and removed from future consideration.

=== Cons

- *More TSP-specific.* Its benefit may not transfer to permutation problems where adjacency is irrelevant.
- *More implementation detail.* Edge tables, shared-edge flags, removal, and tie handling require careful tests.
- *Can become conservative.* When the population has converged to similar edge sets, ERX mostly reuses existing edges and may create little novelty.
- *Tie rules matter.* Different tie-breaking policies can alter diversity, so all experiments must use one documented seeded policy.

=== Implementation plan

Recommended structure:

```text
NeighborInfo:
    neighbors = set of adjacent cities
    shared = subset of edges present in both parents
```

Build adjacency from both cyclic tours in `O(n)`. Each city has at most four distinct parental neighbours, so neighbour inspection is bounded by a small constant.

Efficient implementation complexity:

- time: `O(n)` expected;
- space: `O(n)`.

Avoid an implementation that scans every city to remove the current node. Only update the small number of neighbour lists that can contain it.

Important tests:

- worked example with deterministic tie function;
- every output is a permutation;
- every non-fallback edge should belong to at least one parent;
- shared edge is preferred when the algorithm specification says it should be;
- no infinite loop when all current neighbours are already used;
- identical parents;
- cyclic edge handling (`last <-> first`);
- symmetric undirected edge normalisation.

#line(length: 100%, stroke: 0.4pt + luma(180))

== 4.4 SAX — Structure-Adaptive Crossover (proposed project method)

=== Research hypothesis

A fixed crossover assumes the same preservation behaviour is appropriate for every parent pair. In a diverse population, however, some parents may carry highly complementary edge sets while other pairs may already be structurally similar.

SAX tests the following hypothesis:

#quote(block: true)[
*The crossover mechanism should depend on how much edge structure the two selected parents already share. When parents have highly different edge sets, an edge-preserving operator should exploit their complementary adjacency building blocks; when parents are structurally similar, an order-based operator should provide a less edge-conservative recombination path.*
]

SAX is a project proposal, not a claim of literature novelty. A literature review should be performed before describing it as a novel operator in a paper.

=== Parent edge diversity

For cyclic tours `P1` and `P2`, define undirected edge sets `E(P1)` and `E(P2)`.

```text
D(P1, P2) = 1 - |E(P1) ∩ E(P2)| / n
```

- `D = 0`: parents have identical edge sets.
- `D` close to `1`: parents share few edges.

=== Crossover rule

Use `D` directly as the probability of choosing ERX:

```text
p(ERX) = D(P1, P2)
p(OX)  = 1 - D(P1, P2)
```

Then draw one seeded random value `u`:

```text
if u < D:
    use ERX
else:
    use OX
```

This avoids adding a manually tuned threshold.

=== Why this is a meaningful comparison

SAX is not merely “randomly choose a crossover.” The operator choice is linked to the exact structural feature being studied: *parent edge diversity*.

It also produces an experimentally testable mechanism:

- if SAX behaves like ERX mostly on diverse parent pairs and improves solution quality, this supports the idea that complementary edge sets are useful recombination material;
- if SAX performs no better than fixed OX/ERX, that is evidence that parent-level structural adaptation is unnecessary or that this diversity signal is insufficient.

=== Worked example

Using the same parents:

```text
P1 = [1, 2, 3, 4, 5, 6, 7, 8]
P2 = [4, 1, 2, 8, 7, 6, 5, 3]
```

Undirected P1 edges:

```text
{1-2, 2-3, 3-4, 4-5, 5-6, 6-7, 7-8, 8-1}
```

Undirected P2 edges:

```text
{4-1, 1-2, 2-8, 8-7, 7-6, 6-5, 5-3, 3-4}
```

Shared edges are:

```text
{1-2, 3-4, 5-6, 6-7, 7-8}
```

Therefore:

```text
D = 1 - 5/8 = 0.375
```

So:

```text
p(ERX) = 0.375
p(OX)  = 0.625
```

If the seeded RNG draw is `0.20`, SAX delegates to ERX.
If it is `0.70`, SAX delegates to OX.

The delegated operator then runs exactly as specified above, so validity is inherited from OX/ERX.

=== Pros

- *Directly tied to the research metric.* Edge diversity is not only measured after the run; it actively informs recombination.
- *No arbitrary threshold parameter.* The diversity score itself becomes the ERX probability.
- *Tests a mechanism, not just another operator.* It asks whether crossover should adapt to available parental structure.
- *Low additional implementation cost.* It reuses tested OX, ERX, and edge-set utilities.
- *Keeps the project focused.* Only one proposed method is added to the three conventional comparisons.

=== Cons

- *More difficult causal analysis.* SAX is a mixture of OX and ERX, so results must record which delegate was used each time.
- *The diversity-to-probability mapping is a hypothesis.* `p(ERX)=D` is simple and parameter-free but not theoretically optimal.
- *Still TSP/adjacency biased.* Edge diversity may be the wrong adaptation signal for non-adjacency permutation problems.
- *Can collapse toward one operator.* If population structure makes most `D` values similar, SAX may effectively behave like a fixed mixture.

=== Implementation plan

```text
function SAX(parent1, parent2, rng):
    diversity = edgeDiversity(parent1, parent2)
    if rng() < diversity:
        return ERX(parent1, parent2, rng)
    else:
        return OX(parent1, parent2, rng)
```

Additional experiment metadata should record:

```text
CrossoverEvent:
    operator
    delegatedOperator   // only for SAX
    parentEdgeDiversity
    childEdgePreservation
```

Expected complexity:

- edge diversity: `O(n)`;
- delegated OX/ERX: `O(n)`;
- total: `O(n)` time and `O(n)` space.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 5. Algorithms considered but excluded

== Cycle Crossover (CX) — excluded

CX strongly preserves absolute positions through cycles between parent permutations. PMX already gives the experiment a position-oriented baseline. Adding CX would increase the experimental matrix while contributing a partially overlapping preservation question. It can be added only if the first results suggest that PMX's mapping behaviour is confounding the position-preservation comparison.

== EAX — excluded from the first experiment

Edge Assembly Crossover is highly relevant to high-performance TSP solvers, but it is much more complex than the other selected operators and introduces repair/assembly logic that can dominate the experiment. It is better as a later state-of-the-art follow-up after the simple preservation hypotheses are understood.

== AEX / alternating-edge variants — excluded

They overlap with the adjacency/edge-preserving role already filled by ERX. ERX gives a cleaner initial edge-based comparison.

== Inverse-permutation OX/PMX — excluded

A direct inverse-space implementation does not have a strong label-invariant interpretation for TSP and risks duplicating existing position-based crossover behaviour.

== Large adaptive crossover portfolio — excluded

Using many operators with learned weights would create a credit-assignment problem and add hyperparameters. SAX deliberately uses only OX and ERX so that its mechanism remains interpretable.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 6. Common implementation architecture

Because the public repository does not currently expose an implementation, add a minimal source tree rather than introducing a large framework. The implementation language is intentionally not fixed by this document; the algorithmic interfaces below are language-neutral and can be implemented in TypeScript, Python, Java, C++, Rust, or another suitable language.

Suggested structure:

```text
src/
  ga/
    types
    steadyStateGA
    selection/
      inverseTournament
      randomParent
    crossover/
      CrossoverOperator
      pmx
      ox
      erx
      sax
      helpers
    mutation/
      displacement
    replacement/
      elitist
  tsp/
    instance
    fitness
    edges
  experiments/
    config
    runner
    metrics
    csv

tests/
  crossover/
    pmx.test
    ox.test
    erx.test
    sax.test
    property.test
```

Common interface:

```text
CrossoverOperator:
    name
    crossover(parent1, parent2, rng) -> child
```

For the steady-state `(μ + 1)` algorithm, use a single-child crossover contract so every evaluation corresponds to exactly one generated offspring. This avoids wasting fitness evaluations and keeps the treatment identical across PMX, OX, ERX, and SAX. If an existing implementation already expects two children, keep that architecture only if the same child-selection rule is used for every crossover.

Recommended interface:

```text
CrossoverOperator:
    name
    crossover(parent1, parent2, rng) -> child
```

=== Shared validation

```text
function assertSamePermutation(parent, child):
    assert length(parent) == length(child)
    assert sort(parent) == sort(child)
```

This check is useful in development/tests, but should be disabled in performance-critical experiment loops after the operators are validated.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 7. Controlled experimental methodology

== 7.1 Main experiment

Change only the crossover operator:

```text
PMX
OX
ERX
SAX
```

Keep the following identical across all four configurations.

=== Optimisation problem

Symmetric Euclidean TSP using TSPLIB instances with known optimal tour lengths.

Use the same five medium-sized instances already used/selected by the project/thesis where possible (`n` approximately 262–318). Do not silently substitute instances: record exact TSPLIB names, dimension, and optimum in the experiment config.

=== Population

```text
μ = 200
```

=== Population model

```text
(μ + 1) steady-state GA
```

One offspring is generated, evaluated, and considered for replacement per iteration.

=== Parent selection

To isolate crossover while remaining inside the project's sub-uniform-selection direction:

```text
Parent 1: inverse tournament, k = 2
Parent 2: uniform random selection (RPS), with replacement
```

Inverse tournament is selected for the first implementation because it is simple, tunable, and does not require implementing the more complicated intra-level/hybrid machinery before crossover correctness is established.

After the main crossover experiment is stable, one *secondary validation* may rerun the four crossovers under uniform Parent-1 selection. This is not part of the initial implementation milestone.

=== Mutation

Single-city displacement mutation:

```text
p_mutation = 0.05
```

Choose positions `i != j`, remove the city at `i`, and insert it at `j`.

=== Local search

```text
Disabled in the primary crossover-isolation experiment.
```

Reason: 2-opt can repair or dominate differences created by crossover. The thesis material already motivates a crossover-with-mutation/no-local-search configuration for isolating crossover effects. Local search can be introduced only in a later robustness experiment after the crossover mechanisms are understood.

=== Crossover probability

```text
p_crossover = 1.0
```

Every offspring generation uses the configured crossover. This ensures the experimental treatment is actually applied on every iteration.

=== Elitism / replacement

```text
P <- P ∪ {child}
remove the individual with the worst fitness
```

Tie handling must be deterministic or RNG-seeded and identical across operators.

=== Evaluation budget

Use fitness evaluations rather than traditional generations because the algorithm is steady-state.

Recommended two-stage budget:

```text
Pilot: 100,000 offspring evaluations per run
Main: 500,000 offspring evaluations per run
```

With `μ = 200`, 500,000 offspring evaluations are approximately 2,500 generation-equivalents if one generation-equivalent is defined as `μ` offspring evaluations.

Do not use generation count as the primary stopping rule.

=== Independent runs

```text
30 independent runs per crossover per TSP instance
```

Use exactly the same 30 seed values for every crossover on a given instance.

Suggested seeds:

```text
1000, 1001, ..., 1029
```

Each seed should determine:

- initial population;
- selection draws;
- crossover cut points/ties;
- mutation draws.

For strict common-random-number comparison, pre-generate the initial population from a separate seed stream so every operator begins from the exact same population for a matched run.

=== Stopping criteria

Stop when either:

1. the evaluation budget is exhausted; or
2. the known optimum is reached.

If the optimum is reached, record first-hitting time before stopping.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 8. Metrics and why they matter

== 8.1 Best fitness / optimality gap

For minimisation:

```text
gap = bestTourLength / optimalTourLength - 1
```

Why: raw tour lengths are not comparable across TSPLIB instances. Gap normalises final quality and gives `0` when the optimum is found.

== 8.2 Average population fitness

Record the mean tour length (or normalised gap) of the population at checkpoints.

Why: best fitness alone can hide a weak population containing one lucky elite. Population mean shows whether an operator improves the broader search population.

== 8.3 Success rate

Fraction of runs reaching gap `0`.

Why: distinguishes occasional lucky success from reliable optimisation.

== 8.4 First-hitting time

Number of offspring evaluations needed to first reach the optimum (or a fixed target gap such as `0.1%` if optimum success is too rare).

Why: separates fast convergence from high final success probability.

== 8.5 Runtime

Measure wall-clock runtime and crossover-only CPU time separately if possible.

Why: ERX/SAX may produce better tours but incur more operator overhead than OX/PMX.

Do not compare runtime across machines. Record environment metadata.

== 8.6 Population edge diversity

For two tours:

```text
D(Ti, Tj) = 1 - |E(Ti) ∩ E(Tj)| / n
```

Report mean pairwise edge diversity at fixed evaluation checkpoints.

Why: the research motivation is exploration vs. convergence, and edge diversity is directly relevant to TSP structure.

== 8.7 Edge preservation rate

For child `C`:

```text
edgePreservation(C) =
  |E(C) ∩ (E(P1) ∪ E(P2))| / n
```

Why: directly verifies that ERX actually preserves more parental adjacency than OX/PMX in the implemented system.

== 8.8 Position preservation rate

```text
positionPreservation(C) =
  count(i where C[i] == P1[i] or C[i] == P2[i]) / n
```

Why: verifies the position-preserving behaviour associated with PMX and prevents interpretation based only on operator names.

== 8.9 Parent-child edge distance

Measure edge distance between each child and each parent.

Why: quantifies how disruptive each crossover is and connects exploration directly to offspring generation.

== 8.10 SAX delegation statistics

Record:

- parent edge diversity `D`;
- whether SAX selected OX or ERX;
- child fitness improvement;
- child edge-preservation rate.

Why: SAX can only be explained if its internal choices are observable.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 9. Statistical comparison

Genetic algorithms are stochastic, so one run is not meaningful evidence.

For each instance/operator report:

- mean final optimality gap;
- median final optimality gap;
- standard deviation;
- interquartile range;
- 95% bootstrap confidence interval for the median or mean;
- success rate;
- median first-hitting time for successful runs.

Because the same initial-population seeds are used across algorithms, treat runs with the same seed as matched experimental blocks where practical.

Recommended undergraduate-level significance workflow:

1. *Friedman test* across the four crossovers using matched seed blocks for an instance.
2. If significant, perform pairwise *Wilcoxon signed-rank tests* between crossover pairs.
3. Apply *Holm correction* to the pairwise p-values.
4. Report an effect size as well as p-values; a simple choice is matched median difference or rank-biserial correlation.

Do not claim an operator is superior only because its mean is numerically smaller.

For convergence curves, plot median best-gap versus evaluation count with an uncertainty band (e.g. interquartile range).

#line(length: 100%, stroke: 0.4pt + luma(180))

= 10. Implementation roadmap

== Phase 1 — Verify research configuration

*Objective:* lock representation, fitness, selection, mutation, and stopping rules before crossover coding.

*Files likely affected:*

```text
src/ga/types
src/tsp/instance
src/tsp/fitness
src/experiments/config
```

*Expected output:* TSP instance representation, tour fitness function, seeded RNG contract, experiment config.

*Validation:* known hand-calculated tour lengths; invalid permutation rejected in tests; repeated seed gives identical random sequence.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 2 — Create common crossover interface and helpers

*Objective:* guarantee every crossover plugs into exactly the same GA path.

*Files:*

```text
src/ga/crossover/CrossoverOperator
src/ga/crossover/helpers
src/tsp/edges
```

*Expected output:* interface, cut-point generator, permutation validator, cyclic edge utilities.

*Validation:* utilities pass deterministic unit tests.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 3 — Implement OX

*Objective:* establish the main conventional baseline first.

*Files:*

```text
src/ga/crossover/ox
tests/crossover/ox.test
```

*Expected output:* `O(n)` valid permutation crossover.

*Validation:* worked example plus at least 1,000 seeded random permutation-property cases.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 4 — Implement PMX

*Objective:* add position/mapping comparison.

*Files:*

```text
src/ga/crossover/pmx
tests/crossover/pmx.test
```

*Validation:* worked example; mapping-chain edge cases; 1,000 seeded property cases.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 5 — Implement ERX

*Objective:* add adjacency-preserving comparison.

*Files:*

```text
src/ga/crossover/erx
tests/crossover/erx.test
```

*Validation:* edge table correctness; shared-edge preference; fallback behaviour; 1,000 seeded permutation-property cases.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 6 — Implement the steady-state GA around fixed operators

*Objective:* ensure crossover is the only treatment variable.

*Files:*

```text
src/ga/steadyStateGA
src/ga/selection/inverseTournament
src/ga/selection/randomParent
src/ga/mutation/displacement
src/ga/replacement/elitist
```

*Validation:* fixed seed gives reproducible trajectory; population size always equals `μ`; best fitness never worsens under elitist replacement.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 7 — Implement metrics before SAX

*Objective:* make preservation hypotheses measurable before adding the proposed method.

*Files:*

```text
src/experiments/metrics
src/tsp/edges
```

*Expected output:* optimality gap, edge diversity, position preservation, edge preservation, parent-child distances.

*Validation:* hand-calculated examples.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 8 — Implement SAX

*Objective:* use measured parent edge diversity to choose OX or ERX.

*Files:*

```text
src/ga/crossover/sax
tests/crossover/sax.test
```

*Validation:*

- `D=0` always delegates to OX;
- `D=1` always delegates to ERX;
- intermediate `D` matches expected choice for mocked RNG values;
- child always valid;
- event metadata records delegation.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 9 — Build experiment runner

*Objective:* run every operator under identical settings and export tidy data.

*Files:*

```text
src/experiments/runner
src/experiments/csv
```

*Expected output:* one row per run plus checkpoint metrics.

Minimum run fields:

```text
instance
n
operator
seed
evaluations
bestLength
optimalityGap
success
firstHitEvaluation
runtimeMs
finalEdgeDiversity
```

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 10 — Pilot experiment

*Objective:* catch implementation and instrumentation problems before expensive runs.

Use:

```text
1–2 instances
5 seeds
100,000 evaluations
```

*Validation criteria:* no invalid offspring; reproducible CSV; performance curves are sensible; operator runtime is measured correctly.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 11 — Main controlled experiment

*Objective:* compare PMX, OX, ERX, SAX under the locked configuration.

Use:

```text
5 instances
30 matched seeds
500,000 evaluations per run
```

*Expected output:* final CSV dataset and checkpoint/convergence dataset.

#line(length: 100%, stroke: 0.4pt + luma(180))

== Phase 12 — Statistical analysis

*Objective:* determine whether differences are systematic rather than random.

Output:

- descriptive-statistics table;
- final-gap boxplots;
- median convergence curves;
- edge-diversity curves;
- edge/position preservation comparison;
- Friedman + Holm-corrected Wilcoxon results;
- SAX delegation analysis.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 11. Final experimental architecture

```text
TSPLIB instance
      |
      v
Initial population (same for matched seed)
      |
      v
(μ + 1) steady-state GA
      |
      +--> Parent 1: inverse tournament k=2
      |
      +--> Parent 2: uniform random (RPS)
      |
      v
CROSSOVER TREATMENT
  +-------+-------+-------+-------+
  |       |       |       |       |
 PMX      OX      ERX     SAX
position  order   edges   adaptive OX/ERX
  |       |       |       |
  +-------+-------+-------+
          |
          v
Displacement mutation (p=0.05)
          |
          v
Fitness evaluation
          |
          v
Elitist (μ + 1) replacement
          |
          v
Metrics + checkpoint logging
```

The scientific comparison is therefore:

```text
position preservation
vs.
relative-order preservation
vs.
adjacency preservation
vs.
structure-adaptive preservation
```

while the rest of the GA remains fixed.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 12. Final decision

== Algorithms we will implement

1. *PMX — Partially Mapped Crossover*
2. *OX — Order Crossover*
3. *ERX — Edge Recombination Crossover*
4. *SAX — Structure-Adaptive Crossover (OX/ERX selected from parent edge diversity)*

== Main baseline

*OX* is the main conventional baseline because it is a standard permutation-safe crossover with clear relative-order preservation and low implementation ambiguity.

PMX is retained as the contrasting position/mapping baseline, not as another “general baseline.”

== Proposed research method

*SAX — Structure-Adaptive Crossover.*

It uses parent edge diversity

```text
D = 1 - |E(P1) ∩ E(P2)| / n
```

and sets

```text
p(ERX) = D
p(OX)  = 1 - D
```

so crossover behaviour depends on the structural information available in the selected parent pair.

== Core hypothesis

#quote(block: true)[
For TSP, crossover performance depends on which permutation feature is preserved. Edge-preserving crossover should benefit from adjacency building blocks, order crossover should provide a different form of recombination, and an adaptive operator that uses parent edge diversity may exploit both behaviours more effectively than a single fixed crossover.
]

== Next implementation task

*Implement the common crossover interface and OX first, together with seeded permutation-validity property tests.*

Once OX is correct, implement PMX and ERX against the same interface. Implement SAX only after edge-diversity metrics and both delegate operators are tested.

Do not reopen the crossover-selection stage unless new experimental evidence or supervisor feedback shows that one of these four operators cannot answer the intended research question.

#line(length: 100%, stroke: 0.4pt + luma(180))

= 13. Source notes

The selection above is consistent with the project's public README and the related thesis presentation: steady-state EAs, permutation TSP, low/sub-uniform selective pressure, random second-parent selection, displacement mutation, elitist replacement, optimality gap, and edge diversity form the existing research context.

For crossover taxonomy and preservation behaviour, the design is also consistent with the permutation-operator literature, including work surveying PMX, OX, CX, ERX and related operators and analysing them by permutation features such as positions, relative order, and edges.

Recommended references to cite in the eventual report:

- Gottlieb, J. and Kruse, T. (2000). *Selection in evolutionary algorithms for the traveling salesman problem.*
- Corus, D., Lissovoi, A., Oliveto, P. S., and Witt, C. (2021). *On steady-state evolutionary algorithms and selective pressure: Why inverse rank-based allocation of reproductive trials is best.*
- Cicirello, V. A. (2023). *A Survey and Analysis of Evolutionary Operators for Permutations.*
- Goldberg, D. E. and Lingle, R. (1985). Original PMX work.
- Davis, L. (1985). Original Order Crossover work.
- Whitley, D., Starkweather, T., and Fuquay, D. (1989). Edge recombination work for TSP.
