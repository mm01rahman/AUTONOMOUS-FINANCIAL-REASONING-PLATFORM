"""NFR-003 total-feed-loss chaos verification."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from afrp_runtime.common.statemachine import OperationalState

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_GATE = REPO_ROOT / "tools" / "system_gate.py"


def load_gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("system_gate", SYSTEM_GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GATE = load_gate()


@pytest.fixture(autouse=True)
def _audit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "chaos-test-key")


def test_total_feed_loss_is_vacuous_degraded_not_exception() -> None:
    result = GATE.chaos_total_feed_loss()
    assert result.operational_state is OperationalState.DEGRADED
    assert result.agent_quorum == 0
    assert result.fused_masses == (("THETA", pytest.approx(1.0)),)
    assert result.epistemic_uncertainty == pytest.approx(1.0)
    assert result.trading_permitted is False
