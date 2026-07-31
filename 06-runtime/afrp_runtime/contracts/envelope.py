"""CognitiveEnvelope in-process binding (ADR-0003, REF-001 §1).

Frozen dataclass mirroring ``afrp.v1.CognitiveEnvelope`` field-for-field
(names and numbers documented inline). The proto file remains the wire truth;
parity is asserted by system validation.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Envelope:
    """Universal transport header wrapping every CIO payload."""

    message_id: str  # field 1
    cognitive_cycle_id: str  # field 2
    producer_subsystem_id: str  # field 3
    schema_version: int  # field 4
    semantic_version: int  # field 5
    generated_at_ns: int  # field 6
    mission_profile_id: str  # field 7
    parent_cio_ids: tuple[str, ...]  # field 8
    payload_hash: bytes  # field 9
    trace_id: str  # field 10
    span_id: str  # field 11

    provenance: tuple[str, ...] = field(default=(), compare=False, repr=False)


def hash_payload(payload_repr: str) -> bytes:
    """Canonical payload digest (OBS-05): sha256 over the payload repr."""
    return hashlib.sha256(payload_repr.encode("utf-8")).digest()


def make_envelope(
    producer_subsystem_id: str,
    cognitive_cycle_id: str,
    mission_profile_id: str,
    payload_repr: str,
    parent_cio_ids: tuple[str, ...] = (),
    trace_id: str = "",
    schema_version: int = 1,
    semantic_version: int = 1,
    generated_at_ns: int | None = None,
) -> Envelope:
    """Construct a well-formed envelope with provenance chaining (UX-001)."""
    return Envelope(
        message_id=str(uuid.uuid4()),
        cognitive_cycle_id=cognitive_cycle_id,
        producer_subsystem_id=producer_subsystem_id,
        schema_version=schema_version,
        semantic_version=semantic_version,
        generated_at_ns=time.time_ns() if generated_at_ns is None else generated_at_ns,
        mission_profile_id=mission_profile_id,
        parent_cio_ids=parent_cio_ids,
        payload_hash=hash_payload(payload_repr),
        trace_id=trace_id or str(uuid.uuid4()),
        span_id=str(uuid.uuid4()),
        provenance=(*parent_cio_ids, producer_subsystem_id),
    )
