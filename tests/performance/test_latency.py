"""NFR-001 live Layer 4/5 decision latency benchmark."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

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
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "latency-test-key")


def test_decision_execution_p99_under_50ms() -> None:
    assert GATE.decision_latency_p99(iterations=200) <= 50.0
