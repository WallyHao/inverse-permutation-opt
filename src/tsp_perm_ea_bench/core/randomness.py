"""Stable, explicit seed derivation for reproducible experiment runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SeedDerivation:
    """The versioned inputs used to derive independent random streams."""

    master_seed: int
    instance_id: str
    repeat: int
    schema_version: str = "seed-v1"

    def seed(self, purpose: str) -> int:
        """Derive a stable 64-bit seed for a named stream purpose."""

        return derive_seed(
            self.master_seed,
            self.instance_id,
            self.repeat,
            purpose,
            schema_version=self.schema_version,
        )


def derive_seed(
    master_seed: int,
    instance_id: str,
    repeat: int,
    purpose: str,
    *,
    schema_version: str = "seed-v1",
) -> int:
    """Derive a deterministic seed without relying on process hash randomization."""

    if repeat < 0:
        raise ValueError("repeat must be non-negative")
    payload = json.dumps(
        [schema_version, master_seed, instance_id, repeat, purpose],
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)
