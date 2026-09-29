# Core Protocol

The core package owns run-wide contracts: deterministic seed derivation,
objective-evaluation accounting, and termination semantics. Algorithm code must
use `EvaluationContext.evaluate` for every objective value that influences
search decisions.
