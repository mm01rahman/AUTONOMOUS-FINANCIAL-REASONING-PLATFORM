"""FIT-008 end-to-end MP-04 deterministic replay tests."""

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
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "system-replay-test-key")


def test_mp04_replay_is_bit_exact() -> None:
    first = GATE.semantic_replay()
    second = GATE.semantic_replay()
    assert first == second
    assert first.checksum == second.checksum


def test_mp04_replay_matches_frozen_checksum() -> None:
    snapshot = GATE.semantic_replay()
    expected = GATE.EXPECTED_PATH.read_text(encoding="utf-8").strip()
    assert snapshot.checksum == expected


def test_replay_reaches_all_six_agents_and_null_action() -> None:
    snapshot = GATE.semantic_replay()
    assert len(snapshot.beliefs) == 6
    assert snapshot.world_quorum == 6
    assert len(snapshot.scenario_terminals) > 0
    assert snapshot.action[1:] == (0.0, 0.0)  # MP-04 forbids live trading


def test_edr_012_deprecation_policy_passes() -> None:
    assert GATE.validate_deprecation_policy() == []
