"""Deterministic seed discipline (RT-COMMON, EDR-009 / NFR-004).

Global seed 42. Components derive stable substreams via BLAKE2 keyed
derivation so adding a component never perturbs another component's stream.
"""

from __future__ import annotations

import hashlib
import random

GLOBAL_SEED = 42


def derive_seed(component: str, cycle: int = 0) -> int:
    """Stable 64-bit seed for ``component`` at ``cycle`` under GLOBAL_SEED."""
    digest = hashlib.blake2b(
        f"{GLOBAL_SEED}:{component}:{cycle}".encode(),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, "big")


def component_rng(component: str, cycle: int = 0) -> random.Random:
    """A :class:`random.Random` bound to the component substream."""
    return random.Random(derive_seed(component, cycle))
