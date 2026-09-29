# Benchmark metadata

This directory contains small, version-controlled instances for correctness
and smoke testing. They are not the formal five-instance study suite. The
formal suite remains pending source verification as required by `PLAN.md`.

`manifest.json` records the instance identity, parser protocol, source file
hash, and reference-value status. A reference value is metadata for evaluation
and early stopping; it is never passed to an algorithm as search information.
