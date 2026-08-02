"""DSmT PCR5 evidence fusion core (SLS-300, MATH-001 §2, WP-IMP-0024).

Pure, deterministic library — no I/O, no clocks, no randomness (Article I:
mathematics precedes implementation; EDR-009 determinism).

**Model.** Frame Θ = {BULL, BEAR, RANGE}. Focal elements are canonical
disjunctive normal forms (DNF) over Θ: a frozenset of conjunctions, each
conjunction a frozenset of singletons. The market hybrid DSm model M1
constrains RANGE to be exclusive with direction — RANGE∩BULL = RANGE∩BEAR =
∅ — while the directional paradox BULL∩BEAR remains a valid element
(whipsaw regime), as motivated by GLOSS-001 item 3.

**Combination (two sources).** Conjunctive consensus

    m12(X) = Σ_{A∩B=X} m1(A) · m2(B)

**Conflict redistribution (PCR5).** For every conflicting pair
(X, Y), X∩Y = ∅:

    m(X) += m1(X)²·m2(Y) / (m1(X)+m2(Y)) + m2(X)²·m1(Y) / (m2(X)+m1(Y))

taking each addend only when its denominator is positive. Multi-source
fusion is the sequential left fold of the two-source rule (documented:
PCR5 is not associative; fold order is the canonical agent order).
"""

from __future__ import annotations

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA

__all__ = (
    "FRAME",
    "Element",
    "EMPTY",
    "THETA_ELEMENT",
    "MassFunction",
    "parse_label",
    "render_label",
    "intersect",
    "validate_mass_function",
    "combine_pcr5",
    "combine_all",
    "discount",
    "pignistic",
)

FRAME: tuple[str, ...] = ("BULL", "BEAR", "RANGE")

# A focal element in canonical DNF: frozenset of conjunctions.
Element = frozenset[frozenset[str]]

EMPTY: Element = frozenset()
THETA_ELEMENT: Element = frozenset(frozenset({s}) for s in FRAME)

# Hybrid model M1 integrity constraints: conjunctions that collapse to ∅.
_CONSTRAINED: tuple[frozenset[str], ...] = (
    frozenset({"RANGE", "BULL"}),
    frozenset({"RANGE", "BEAR"}),
)

MassFunction = dict[str, float]
_EPS = 1e-12


def _apply_constraints(conjunctions: set[frozenset[str]]) -> set[frozenset[str]]:
    return {
        conj
        for conj in conjunctions
        if not any(constraint <= conj for constraint in _CONSTRAINED)
    }


def _minimalize(conjunctions: set[frozenset[str]]) -> Element:
    """Absorption: a ∪ (a∧b) = a — keep only minimal conjunctions."""
    minimal = {
        conj
        for conj in conjunctions
        if not any(other < conj for other in conjunctions)
    }
    return frozenset(minimal)


def parse_label(label: str) -> Element:
    """Parse a canonical focal label into DNF.

    Grammar: THETA | branch ('|' branch)* with branch = SINGLETON ('&'
    SINGLETON)*.

    Raises:
        ContractViolationError: unknown singleton or empty/constrained result.
    """
    if label == THETA:
        return THETA_ELEMENT
    conjunctions: set[frozenset[str]] = set()
    for branch in label.split("|"):
        parts = branch.split("&")
        for part in parts:
            if part not in FRAME:
                raise ContractViolationError(
                    "CIO-03", f"unknown frame element {part!r} in label {label!r}"
                )
        conjunctions.add(frozenset(parts))
    element = _minimalize(_apply_constraints(conjunctions))
    if not element:
        raise ContractViolationError(
            "CIO-03", f"label {label!r} is constrained empty under model M1"
        )
    return element


def render_label(element: Element) -> str:
    """Render an element back to its canonical label."""
    if element == THETA_ELEMENT:
        return THETA
    branches = sorted("&".join(sorted(conj)) for conj in element)
    return "|".join(branches)


def intersect(x: Element, y: Element) -> Element:
    """DNF intersection under model M1 constraints (may be EMPTY)."""
    combined = {a | b for a in x for b in y}
    return _minimalize(_apply_constraints(combined))


def validate_mass_function(masses: MassFunction) -> dict[Element, float]:
    """Parse and validate a labeled BBA into element space.

    Raises:
        ContractViolationError: negative mass, non-unit sum, or bad label.
    """
    parsed: dict[Element, float] = {}
    for label, value in masses.items():
        if value < 0.0:
            raise ContractViolationError("CIO-03", f"negative mass on {label!r}")
        element = parse_label(label)
        parsed[element] = parsed.get(element, 0.0) + value
    total = sum(parsed.values())
    if abs(total - 1.0) > 1e-9:
        raise ContractViolationError("CIO-03", f"masses sum to {total!r}, not 1.0")
    return parsed


def _to_labels(parsed: dict[Element, float]) -> MassFunction:
    out = {
        render_label(element): value
        for element, value in parsed.items()
        if value > _EPS
    }
    return dict(sorted(out.items()))


def combine_pcr5(m1: MassFunction, m2: MassFunction) -> tuple[MassFunction, float]:
    """Two-source PCR5 combination.

    Returns ``(fused_masses, conflict_mass)`` where ``conflict_mass`` is the
    total conjunctive conflict k12 that was redistributed.
    """
    p1 = validate_mass_function(m1)
    p2 = validate_mass_function(m2)

    fused: dict[Element, float] = {}
    conflict_total = 0.0

    for a, mass_a in p1.items():
        for b, mass_b in p2.items():
            product = mass_a * mass_b
            if product <= 0.0:
                continue
            meet = intersect(a, b)
            if meet:
                fused[meet] = fused.get(meet, 0.0) + product
            else:
                conflict_total += product
                # PCR5 proportional redistribution to the two conflicting
                # focal elements (MATH-001 §2).
                d1 = mass_a + mass_b
                if d1 > 0.0:
                    fused[a] = fused.get(a, 0.0) + mass_a**2 * mass_b / d1
                    fused[b] = fused.get(b, 0.0) + mass_b**2 * mass_a / d1

    total = sum(fused.values())
    if total <= 0.0:
        raise ContractViolationError("CIO-04", "fusion produced zero total mass")
    normalized = {element: value / total for element, value in fused.items()}
    return _to_labels(normalized), conflict_total


def combine_all(sources: list[MassFunction]) -> tuple[MassFunction, float]:
    """Sequential PCR5 fold over ``sources`` in given order.

    Returns ``(fused, total_conflict)`` where total_conflict accumulates the
    per-step redistributed conflict.

    Raises:
        ContractViolationError: no sources supplied.
    """
    if not sources:
        raise ContractViolationError("CIO-04", "no belief sources to fuse")
    fused = dict(sources[0])
    validate_mass_function(fused)
    conflict_total = 0.0
    for source in sources[1:]:
        fused, conflict = combine_pcr5(fused, source)
        conflict_total += conflict
    return dict(sorted(fused.items())), conflict_total


def discount(masses: MassFunction, weight: float) -> MassFunction:
    """Shafer reliability discounting toward Θ (CIO-11 weights).

    m_w(X) = w·m(X) for X ≠ Θ;  m_w(Θ) = w·m(Θ) + (1 − w).

    Raises:
        ContractViolationError: weight outside [0, 1].
    """
    if not 0.0 <= weight <= 1.0:
        raise ContractViolationError("CIO-11", f"weight {weight} outside [0, 1]")
    discounted = {
        label: value * weight for label, value in masses.items() if label != THETA
    }
    discounted[THETA] = masses.get(THETA, 0.0) * weight + (1.0 - weight)
    return dict(sorted((k, v) for k, v in discounted.items() if v > _EPS))


def pignistic(masses: MassFunction) -> dict[str, float]:
    """Generalized pignistic transform onto the singletons.

    Union branches split mass equally across branches; a paradox conjunction
    splits equally across its member singletons (DSmT GPT for 2-paradoxes).
    """
    betp = {singleton: 0.0 for singleton in FRAME}
    for label, value in masses.items():
        element = parse_label(label)
        branch_share = value / len(element)
        for conj in element:
            member_share = branch_share / len(conj)
            for singleton in conj:
                betp[singleton] += member_share
    return betp
