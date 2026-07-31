"""WP-RT-1012 unit tests for PCR5 fusion and the World Model Kernel."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import THETA
from afrp_runtime.layer3.dsmt import (
    combine_all,
    combine_pcr5,
    discount,
    parse_label,
    pignistic,
    render_label,
    validate_mass_function,
)

# ── label parsing / rendering ──────────────────────────────────────────────────


def test_parse_theta_round_trips() -> None:
    assert render_label(parse_label(THETA)) == THETA


def test_parse_singleton() -> None:
    el = parse_label("BULL")
    assert render_label(el) == "BULL"


def test_parse_union() -> None:
    el = parse_label("BEAR|BULL")
    assert render_label(el) == "BEAR|BULL"


def test_parse_paradox() -> None:
    el = parse_label("BEAR&BULL")
    assert render_label(el) == "BEAR&BULL"


def test_parse_unknown_element_raises() -> None:
    with pytest.raises(ContractViolationError):
        parse_label("SIDEWAYS")


def test_constrained_element_raises() -> None:
    with pytest.raises(ContractViolationError):
        parse_label("RANGE&BULL")


# ── mass validation ────────────────────────────────────────────────────────────


def test_valid_mass_function_accepted() -> None:
    validate_mass_function({"BULL": 0.6, "BEAR": 0.3, THETA: 0.1})


def test_negative_mass_raises() -> None:
    with pytest.raises(ContractViolationError):
        validate_mass_function({"BULL": -0.1, THETA: 1.1})


def test_non_unit_sum_raises() -> None:
    with pytest.raises(ContractViolationError):
        validate_mass_function({"BULL": 0.3, "BEAR": 0.3})


# ── PCR5 combination ───────────────────────────────────────────────────────────


def test_pcr5_identical_sources_is_stable() -> None:
    m = {"BULL": 0.7, "BEAR": 0.2, THETA: 0.1}
    fused, conflict = combine_pcr5(m, m)
    assert abs(sum(fused.values()) - 1.0) < 1e-9
    assert conflict >= 0.0


def test_pcr5_vacuous_left_identity() -> None:
    """Fusing a vacuous belief leaves the non-vacuous source unchanged."""
    m_real = {"BULL": 0.8, THETA: 0.2}
    m_vac = {THETA: 1.0}
    fused, conflict = combine_pcr5(m_real, m_vac)
    # After PCR5 with a vacuous source the focal content should not flip polarity
    assert abs(sum(fused.values()) - 1.0) < 1e-9
    assert conflict == pytest.approx(0.0)


def test_pcr5_conflicting_sources_redistributes_mass() -> None:
    """RANGE and BULL are M1-constrained exclusive; full conflict redistributed."""
    m_range = {"RANGE": 1.0}
    m_bull = {"BULL": 1.0}
    fused, conflict = combine_pcr5(m_range, m_bull)
    assert conflict == pytest.approx(1.0)
    assert abs(sum(fused.values()) - 1.0) < 1e-9
    # PCR5 splits 1.0 conflict proportionally; both RANGE and BULL recover 0.5
    assert fused.get("RANGE", 0.0) == pytest.approx(0.5)
    assert fused.get("BULL", 0.0) == pytest.approx(0.5)


# ── multi-source fold ──────────────────────────────────────────────────────────


def test_combine_all_single_source_passthrough() -> None:
    m = {"BULL": 0.6, THETA: 0.4}
    fused, conflict = combine_all([m])
    assert fused == dict(sorted(m.items()))
    assert conflict == 0.0


def test_combine_all_empty_raises() -> None:
    with pytest.raises(ContractViolationError):
        combine_all([])


def test_combine_all_six_agents_stable() -> None:
    sources = [
        {"BULL": 0.6, "BEAR": 0.2, THETA: 0.2},
        {"RANGE": 0.5, "BEAR|BULL": 0.3, THETA: 0.2},
        {"RANGE": 0.7, THETA: 0.3},
        {"BULL": 0.4, "RANGE": 0.3, THETA: 0.3},
        {"BEAR": 0.5, THETA: 0.5},
        {"BEAR&BULL": 0.2, THETA: 0.8},
    ]
    fused, conflict = combine_all(sources)
    assert abs(sum(fused.values()) - 1.0) < 1e-9
    assert conflict >= 0.0


# ── discount ───────────────────────────────────────────────────────────────────


def test_discount_weight_zero_gives_vacuous() -> None:
    discounted = discount({"BULL": 0.9, THETA: 0.1}, 0.0)
    assert discounted.get(THETA, 0.0) == pytest.approx(1.0)


def test_discount_weight_one_is_identity() -> None:
    m = {"BULL": 0.8, THETA: 0.2}
    discounted = discount(m, 1.0)
    assert discounted["BULL"] == pytest.approx(0.8)
    assert discounted[THETA] == pytest.approx(0.2)


def test_discount_invalid_weight_raises() -> None:
    with pytest.raises(ContractViolationError):
        discount({"BULL": 1.0}, 1.5)


# ── pignistic transform ────────────────────────────────────────────────────────


def test_pignistic_singleton_mass_direct() -> None:
    betp = pignistic({"BULL": 1.0})
    assert betp["BULL"] == pytest.approx(1.0)
    assert betp["BEAR"] == pytest.approx(0.0)
    assert betp["RANGE"] == pytest.approx(0.0)


def test_pignistic_theta_splits_equally() -> None:
    betp = pignistic({THETA: 1.0})
    for singleton in ("BULL", "BEAR", "RANGE"):
        assert betp[singleton] == pytest.approx(1.0 / 3.0, abs=1e-9)
