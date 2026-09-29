"""Problem definitions, parsers, and structural metrics."""

from .tsp import (
    ProblemFormatError,
    ReferenceStatus,
    TSPProblem,
    load_tsplib,
)
from .registry import InstanceRecord, InstanceRegistry

__all__ = [
    "InstanceRecord",
    "InstanceRegistry",
    "ProblemFormatError",
    "ReferenceStatus",
    "TSPProblem",
    "load_tsplib",
]
