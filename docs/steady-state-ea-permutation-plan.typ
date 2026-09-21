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
