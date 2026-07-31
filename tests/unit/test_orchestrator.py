"""Unit tests for WP-IMP-0008: RSM-1.0 lifecycle and the afrp run orchestrator."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from afrp.cli import cli
from afrp.core.exceptions import InvariantError
from afrp.core.lifecycle import LifecycleMachine, LifecycleState, legal_transitions
from afrp.core.orchestrator import evaluate_precondition, orchestrate, run_gate
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def synthetic_wp(gate_command: str) -> dict[str, Any]:
    return {
        "schema_version": "WPS-1.0",
        "work_package_id": "WP-TST-0001",
        "capability_id": {"id": "TST-CAP", "version": "1.0"},
        "title": "Synthetic orchestrator fixture",
        "status": "Assigned",
        "is_immutable": True,
        "governance": {
            "target_subsystem": "TEST",
            "traceability": {"implements_req": ["FR-TEST"]},
        },
        "preconditions": [
            {"predicate": "file.exists('README.md')"},
            {"predicate": "git.tag == 'fixture-start'"},
            {"predicate": "capability.complete('TST-DEP')"},
        ],
        "resources": {"filesystem": {"write": ["src/"], "read": ["README.md"]}},
        "execution": {"priority": "low", "deterministic": True},
        "rollback": {"strategy": "git_checkout_bounded_files", "restore_tag": "HEAD"},
        "inputs": {"required_files": ["README.md"]},
        "outputs": {
            "expected_source_files": ["src/mod.py"],
            "expected_evidence": ["05-work-packages/WP-TST-0001/evidence/EXEC-900.yaml"],
        },
        "produces": {
            "capability": {"id": "TST-CAP", "version": "1.0"},
            "unlocks": [],
        },
        "scope": {"bounded_files": ["src/mod.py"]},
        "requirements": {},
        "quality_gates": {
            "smoke": {"required": True, "command": gate_command},
        },
        "completion": {"success_requires": ["gates pass"]},
        "failure_modes": {"ERR-GATE-FAILURE": "smoke gate failed"},
    }


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    """A synthetic governed repository with one committed source file."""
    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    gov = tmp_path / "00-governance"
    gov.mkdir()
    (gov / "BASELINE_FINGERPRINT.yaml").write_text(
        "schema_version: '1.0'\nartifacts: []\n", encoding="utf-8"
    )
    schemas = tmp_path / "09-validation" / "schemas"
    schemas.mkdir(parents=True)
    for name in ("wps-1.0.schema.json", "ers-1.0.schema.json"):
        (schemas / name).write_text(
            (REPO_ROOT / "09-validation" / "schemas" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    eng = tmp_path / "03-engineering"
    eng.mkdir()
    (eng / "CAPABILITY_REGISTRY.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "registry_id": "CAPABILITY_REGISTRY",
                "capabilities": [
                    {
                        "id": "TST-DEP",
                        "version": "1.0",
                        "title": "dep",
                        "owner": "TEST",
                        "status": "COMPLETE",
                        "depends_on": [],
                        "work_package": None,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    wp_dir = tmp_path / "05-work-packages"
    wp_dir.mkdir()
    (wp_dir / "WP-TST-0001.yaml").write_text(
        yaml.safe_dump(synthetic_wp("python -c \"pass\""), sort_keys=False),
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    git("init", "-q")
    git("add", ".")
    git("commit", "-q", "-m", "fixture root")
    git("tag", "fixture-start")
    return tmp_path


class TestLifecycleMachine:
    def test_full_legal_path(self) -> None:
        machine = LifecycleMachine()
        path = [
            LifecycleState.BASELINE_VERIFIED,
            LifecycleState.WORK_PACKAGE_LOADED,
            LifecycleState.PRECONDITIONS_VERIFIED,
            LifecycleState.EXECUTION_AUTHORIZED,
            LifecycleState.EXECUTING,
            LifecycleState.VALIDATING,
            LifecycleState.EVIDENCE_GENERATED,
            LifecycleState.REVIEW_PENDING,
            LifecycleState.COMPLETED,
        ]
        for state in path:
            machine.advance(state)
        assert machine.terminal
        assert [s for s, _ in machine.history][1:] == path

    def test_illegal_jump_rejected(self) -> None:
        machine = LifecycleMachine()
        with pytest.raises(InvariantError, match="RSM-1.0"):
            machine.advance(LifecycleState.EXECUTING)

    def test_halt_reachable_from_any_live_state(self) -> None:
        machine = LifecycleMachine()
        machine.advance(LifecycleState.BASELINE_VERIFIED)
        machine.halt("test halt")
        assert machine.state is LifecycleState.HALTED
        assert machine.terminal

    def test_terminal_states_are_dead_ends(self) -> None:
        assert legal_transitions(LifecycleState.COMPLETED) == ()
        assert legal_transitions(LifecycleState.HALTED) == ()

    def test_no_resurrection_after_halt(self) -> None:
        machine = LifecycleMachine()
        machine.halt("dead")
        with pytest.raises(InvariantError):
            machine.advance(LifecycleState.BASELINE_VERIFIED)


class TestPreconditions:
    def test_file_exists_predicates(self, fixture_repo: Path) -> None:
        ok = evaluate_precondition(fixture_repo, "file.exists('README.md')")
        missing = evaluate_precondition(fixture_repo, "file.exists('GHOST.md')")
        assert ok.passed and not missing.passed

    def test_git_tag_predicates(self, fixture_repo: Path) -> None:
        ok = evaluate_precondition(fixture_repo, "git.tag == 'fixture-start'")
        missing = evaluate_precondition(fixture_repo, "git.tag == 'no-such-tag'")
        assert ok.passed and not missing.passed

    def test_capability_complete_predicate(self, fixture_repo: Path) -> None:
        ok = evaluate_precondition(fixture_repo, "capability.complete('TST-DEP')")
        missing = evaluate_precondition(fixture_repo, "capability.complete('GHOST')")
        assert ok.passed and not missing.passed

    def test_unknown_grammar_rejected(self, fixture_repo: Path) -> None:
        with pytest.raises(InvariantError, match="grammar"):
            evaluate_precondition(fixture_repo, "moon.phase == 'full'")


class TestGateExecution:
    def test_passing_gate(self, fixture_repo: Path) -> None:
        outcome = run_gate(fixture_repo, "smoke", 'python -c "print(42)"')
        assert outcome.passed

    def test_failing_gate(self, fixture_repo: Path) -> None:
        outcome = run_gate(fixture_repo, "smoke", 'python -c "raise SystemExit(2)"')
        assert not outcome.passed


class TestOrchestrator:
    def test_happy_path_reaches_review_pending(self, fixture_repo: Path) -> None:
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.REVIEW_PENDING
        assert all(p.passed for p in report.preconditions)
        assert all(g.passed for g in report.gates)
        assert report.boundary_violations == ()
        states = [s for s, _ in report.transitions]
        assert states[0] == "INITIAL" and states[-1] == "REVIEW_PENDING"

    def test_dry_run_stops_before_execution(self, fixture_repo: Path) -> None:
        report = orchestrate(fixture_repo, "WP-TST-0001", dry_run=True)
        assert report.final_state is LifecycleState.HALTED
        states = [s for s, _ in report.transitions]
        assert "EXECUTION_AUTHORIZED" in states
        assert "EXECUTING" not in states
        assert report.gates == ()

    def test_failing_gate_rolls_back_bounded_files(self, fixture_repo: Path) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "raise SystemExit(1)"'), sort_keys=False
            ),
            encoding="utf-8",
        )
        target = fixture_repo / "src" / "mod.py"
        target.write_text("VALUE = 999  # engineer draft\n", encoding="utf-8")
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert target.read_text(encoding="utf-8") == "VALUE = 1\n"  # rolled back

    def test_precondition_failure_halts_zero_write(self, fixture_repo: Path) -> None:
        (fixture_repo / "README.md").unlink()
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert any(not p.passed for p in report.preconditions)
        assert report.gates == ()

    def test_out_of_bounds_write_halts(self, fixture_repo: Path) -> None:
        (fixture_repo / "rogue.py").write_text("x = 1\n", encoding="utf-8")
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "rogue.py" in report.boundary_violations

    def test_missing_wp_halts(self, fixture_repo: Path) -> None:
        report = orchestrate(fixture_repo, "WP-TST-4242")
        assert report.final_state is LifecycleState.HALTED
        assert report.halted_reason is not None

    def test_tampered_baseline_halts_before_load(self, fixture_repo: Path) -> None:
        ledger = fixture_repo / "00-governance" / "BASELINE_FINGERPRINT.yaml"
        ledger.write_text(
            "schema_version: '1.0'\nartifacts:\n"
            "  - path: 'README.md'\n"
            f"    sha256: '{'0' * 64}'\n",
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        states = [s for s, _ in report.transitions]
        assert "WORK_PACKAGE_LOADED" not in states


class TestRunCommand:
    def test_cli_dry_run_on_real_repository(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["run", "--wp", "WP-IMP-0008", "--dry-run", "--repo-root", str(REPO_ROOT)]
        )
        assert outcome.exit_code == 0, outcome.output
        assert "EXECUTION_AUTHORIZED" in outcome.output
        assert "final_state: HALTED" in outcome.output  # dry-run terminates via halt

    def test_cli_full_run_on_fixture(self, fixture_repo: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["run", "--wp", "WP-TST-0001", "--repo-root", str(fixture_repo)]
        )
        assert outcome.exit_code == 0, outcome.output
        assert "final_state: REVIEW_PENDING" in outcome.output

    def test_cli_halt_exit_code(self, fixture_repo: Path) -> None:
        (fixture_repo / "README.md").unlink()
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["run", "--wp", "WP-TST-0001", "--repo-root", str(fixture_repo)]
        )
        assert outcome.exit_code == 3
