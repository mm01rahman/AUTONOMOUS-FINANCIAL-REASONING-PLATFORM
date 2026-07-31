"""WP-RT-1005 unit tests for Layer 2 base and DSmT mass primitives."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA
from afrp_runtime.layer2.base import (
    intersection_label,
    normalize_masses,
    pad_ignorance,
    union_label,
    vacuous_bba,
)


def test_union_canonical_ordering() -> None:
    assert union_label("BULL", "BEAR") == "BEAR|BULL"
    assert union_label("BEAR", "BULL") == "BEAR|BULL"


def test_intersection_canonical_ordering() -> None:
    assert intersection_label("BULL", "BEAR") == "BEAR&BULL"


def test_unknown_elements_rejected() -> None:
    with pytest.raises(ContractViolationError):
        union_label("BULL", "SIDEWAYS")


def test_normalize_masses_sums_to_one() -> None:
    masses = normalize_masses({"BULL": 2.0, "BEAR": 1.0, THETA: 1.0})
    assert sum(masses.values()) == pytest.approx(1.0)
    assert masses["BULL"] == pytest.approx(0.5)


def test_negative_mass_rejected() -> None:
    with pytest.raises(ContractViolationError):
        normalize_masses({"BULL": -0.1, THETA: 1.1})


def test_zero_total_rejected() -> None:
    with pytest.raises(ContractViolationError):
        normalize_masses({"BULL": 0.0})


def test_vacuous_is_pure_theta() -> None:
    assert vacuous_bba() == {THETA: 1.0}


def test_pad_ignorance_is_deterministic() -> None:
    padded = pad_ignorance({"BULL": 1.0}, confidence=0.6)
    assert padded["BULL"] == pytest.approx(0.6)
    assert padded[THETA] == pytest.approx(0.4)
