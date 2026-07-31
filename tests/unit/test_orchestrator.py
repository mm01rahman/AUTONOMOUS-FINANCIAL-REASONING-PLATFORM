"""Unit tests for WP-IMP-0008: RSM-1.0 lifecycle and the afrp run orchestrator."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from afrp.cli import cli
from afrp.core.evidence import load_evidence
from afrp.core.exceptions import InvariantError
from afrp.core.lifecycle import LifecycleMachine, LifecycleState, legal_transitions
from afrp.core.orchestrator import (
    _workspace_lock,
    evaluate_precondition,
    orchestrate,
    run_gate,
)
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


TASK_COMMAND = [
    "python",
    "-c",
    (
        "from pathlib import Path; "
        "Path('src/mod.py').write_text('VALUE = 2\\n', encoding='utf-8')"
    ),
]


def synthetic_wp(
    gate_command: str, task_command: str | list[str] | None = TASK_COMMAND
) -> dict[str, Any]:
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
        "execution": {
            "priority": "low",
            "deterministic": True,
            **({"command": task_command} if task_command is not None else {}),
        },
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
        "scope": {
            "bounded_files": [
                "src/mod.py",
                "src/generated/",
                "05-work-packages/WP-TST-0001/evidence/",
            ]
        },
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
    (tmp_path / ".gitignore").write_text("*.ignored\n.venv/\n", encoding="utf-8")
    readme_digest = hashlib.sha256((tmp_path / "README.md").read_bytes()).hexdigest()
    gov = tmp_path / "00-governance"
    gov.mkdir()
    (gov / "BASELINE_FINGERPRINT.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "ledger_id": "BASELINE_FINGERPRINT",
                "baseline_id": "AFRP-BASELINE-1.0.0",
                "hash_algorithm": "sha256",
                "generated_at": "2026-07-31T15:45:18+00:00",
                "artifacts": [{"path": "README.md", "sha256": readme_digest}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
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
        assert report.final_state is LifecycleState.REVIEW_PENDING, report.halted_reason
        assert all(p.passed for p in report.preconditions)
        assert all(g.passed for g in report.gates)
        assert report.boundary_violations == ()
        states = [s for s, _ in report.transitions]
        assert states[0] == "INITIAL" and states[-1] == "REVIEW_PENDING"
        assert (fixture_repo / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 2\n"
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        record = load_evidence(fixture_repo, evidence)
        assert record["verdict"]["all_gates_passed"] is True
        assert record["verdict"]["review_status"] == "PENDING_ARB"

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
        assert target.read_text(encoding="utf-8") == "VALUE = 999  # engineer draft\n"
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        record = load_evidence(fixture_repo, evidence)
        assert record["lifecycle"]["final_state"] == "HALTED"
        assert record["quality_gates"][0]["result"] == "FAIL"
        assert record["verdict"]["all_gates_passed"] is False

    def test_gate_cannot_remove_expected_output(self, fixture_repo: Path) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    "python -c \"from pathlib import Path; "
                    "Path('src/mod.py').unlink()\""
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "missing: src/mod.py" in (report.halted_reason or "")
        assert (fixture_repo / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"

    def test_task_failure_rolls_back_and_emits_halted_evidence(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    'python -c "pass"',
                    [
                        "python",
                        "-c",
                        (
                            "from pathlib import Path; "
                            "Path('src/new.py').write_text('new'); "
                            "raise SystemExit(7)"
                        ),
                    ],
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert not (fixture_repo / "src" / "new.py").exists()
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        record = load_evidence(fixture_repo, evidence)
        assert record["lifecycle"]["final_state"] == "HALTED"
        assert all(gate["result"] == "SKIPPED" for gate in record["quality_gates"])

    def test_rollback_failure_still_emits_truthful_halted_evidence(
        self, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    'python -c "pass"',
                    ["python", "-c", "raise SystemExit(9)"],
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        def fail_restore(repo_root: Path, snapshot: object) -> None:
            raise OSError(f"simulated restore failure in {repo_root}: {snapshot!r}")

        monkeypatch.setattr(
            "afrp.core.orchestrator._restore_git_control", fail_restore
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "rollback FAILED" in (report.halted_reason or "")
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        record = load_evidence(fixture_repo, evidence)
        assert record["lifecycle"]["final_state"] == "HALTED"
        assert "rollback FAILED" in record["verdict"]["review_note"]

    def test_precondition_failure_halts_zero_write(self, fixture_repo: Path) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        document = synthetic_wp('python -c "pass"')
        document["preconditions"][0]["predicate"] = "file.exists('GHOST.md')"
        wp_path.write_text(
            yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert any(not p.passed for p in report.preconditions)
        assert report.gates == ()

    def test_out_of_bounds_write_halts(self, fixture_repo: Path) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    'python -c "pass"',
                    [
                        "python",
                        "-c",
                        "from pathlib import Path; Path('rogue.py').write_text('x = 1\\n')",
                    ],
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "rogue.py" in report.boundary_violations
        assert not (fixture_repo / "rogue.py").exists()

    def test_skip_gates_is_rejected(self, fixture_repo: Path) -> None:
        report = orchestrate(fixture_repo, "WP-TST-0001", skip_gates=True)
        assert report.final_state is LifecycleState.HALTED
        assert report.gates == ()
        assert "prohibited" in (report.halted_reason or "")

    def test_missing_task_command_halts_before_executing(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', None), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "EXECUTING" not in [state for state, _ in report.transitions]
        assert (fixture_repo / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        record = load_evidence(fixture_repo, evidence)
        assert record["lifecycle"]["final_state"] == "HALTED"
        assert all(gate["result"] == "SKIPPED" for gate in record["quality_gates"])

    def test_invalid_command_halts_with_evidence_before_executing(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', 'python -c "unterminated'),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "EXECUTING" not in [state for state, _ in report.transitions]
        assert "invalid command quoting" in (report.halted_reason or "")
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        assert load_evidence(fixture_repo, evidence)["lifecycle"]["final_state"] == "HALTED"

    def test_nul_command_halts_with_evidence_before_executing(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', ["bad\x00command"]),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "EXECUTING" not in [state for state, _ in report.transitions]
        assert "must not contain NUL" in (report.halted_reason or "")
        evidence = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        assert load_evidence(fixture_repo, evidence)["lifecycle"]["final_state"] == "HALTED"

    def test_noop_command_cannot_satisfy_expected_outputs(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', ["python", "-c", "pass"]),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "not changed by task: src/mod.py" in (report.halted_reason or "")

    def test_missing_expected_output_halts_and_rolls_back(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        document = synthetic_wp('python -c "pass"')
        document["outputs"]["expected_source_files"] = ["src/missing.py"]
        document["scope"]["bounded_files"].append("src/missing.py")
        wp_path.write_text(
            yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "missing: src/missing.py" in (report.halted_reason or "")
        assert (fixture_repo / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"

    def test_lock_contention_halts(self, fixture_repo: Path) -> None:
        lock = fixture_repo / ".git" / "afrp-orchestrator.lock"
        lock.write_text("held\n", encoding="utf-8")
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "already held" in (report.halted_reason or "")
        assert lock.exists()

    def test_lock_supports_current_git_worktree(self) -> None:
        assert (REPO_ROOT / ".git").is_file()
        with _workspace_lock(REPO_ROOT):
            common_dir = Path(
                subprocess.run(
                    ["git", "rev-parse", "--git-common-dir"],
                    cwd=REPO_ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
            )
            if not common_dir.is_absolute():
                common_dir = REPO_ROOT / common_dir
            lock_path = common_dir.resolve() / "afrp-orchestrator.lock"
            assert lock_path.is_file()
            worktree_lock = subprocess.run(
                ["git", "rev-parse", "--git-path", "afrp-orchestrator.lock"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            assert lock_path != Path(worktree_lock)
        assert not lock_path.exists()

    def test_lock_is_held_during_gate_execution(self, fixture_repo: Path) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    "python -c \"from pathlib import Path; "
                    "assert Path('.git/afrp-orchestrator.lock').is_file()\""
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.REVIEW_PENDING
        assert not (fixture_repo / ".git" / "afrp-orchestrator.lock").exists()

    def test_gate_tooling_artifacts_are_cleaned_without_false_fit_failure(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    "python -c \"from pathlib import Path; "
                    "Path('.pytest_cache').mkdir(); "
                    "Path('.pytest_cache/state').write_text('gate'); "
                    "Path('__pycache__').mkdir(); "
                    "Path('__pycache__/mod.pyc').write_text('gate')\""
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.REVIEW_PENDING, report.halted_reason
        assert not (fixture_repo / ".pytest_cache").exists()
        assert not (fixture_repo / "__pycache__").exists()

    def test_fit_failure_rolls_back_new_trees_and_preserves_preexisting(
        self, fixture_repo: Path
    ) -> None:
        preexisting = fixture_repo / "draft.txt"
        preexisting.write_text("keep me\n", encoding="utf-8")
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        command = [
            "python",
            "-c",
            (
                "from pathlib import Path; "
                "Path('src/generated/deep').mkdir(parents=True); "
                "Path('src/generated/deep/new.py').write_text('new\\n'); "
                "Path('outside/tree').mkdir(parents=True); "
                "Path('outside/tree/rogue.py').write_text('rogue\\n')"
            ),
        ]
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "outside/tree/rogue.py" in report.boundary_violations
        assert not (fixture_repo / "src" / "generated").exists()
        assert not (fixture_repo / "outside").exists()
        assert preexisting.read_text(encoding="utf-8") == "keep me\n"

    def test_shell_metacharacters_are_not_interpreted(
        self, fixture_repo: Path
    ) -> None:
        command = (
            "python -c \"from pathlib import Path; "
            "Path('src/mod.py').write_text('SAFE = True\\\\n')\" "
            "; python -c \"from pathlib import Path; Path('rogue.py').write_text('bad')\""
        )
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.REVIEW_PENDING
        assert not (fixture_repo / "rogue.py").exists()

    def test_ignored_out_of_bounds_file_is_rolled_back(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp(
                    'python -c "pass"',
                    [
                        "python",
                        "-c",
                        "from pathlib import Path; Path('rogue.ignored').write_text('bad')",
                    ],
                ),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "rogue.ignored" in report.boundary_violations
        assert not (fixture_repo / "rogue.ignored").exists()

    def test_task_created_ignored_environment_is_removed(
        self, fixture_repo: Path
    ) -> None:
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        command = [
            "python",
            "-c",
            (
                "from pathlib import Path; "
                "Path('src/mod.py').write_text('VALUE = 2\\n'); "
                "Path('.venv/bin').mkdir(parents=True); "
                "Path('.venv/bin/tool').write_text('task-created')"
            ),
        ]
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert ".venv/bin/tool" in report.boundary_violations
        assert not (fixture_repo / ".venv").exists()

    def test_index_config_and_hook_mutation_is_prohibited_and_restored(
        self, fixture_repo: Path
    ) -> None:
        target = fixture_repo / "src" / "mod.py"
        target.write_text("VALUE = 7  # preexisting staged\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/mod.py"], cwd=fixture_repo, check=True)
        original_index = subprocess.run(
            ["git", "show", ":src/mod.py"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        command = [
            "python",
            "-c",
            (
                "from pathlib import Path; import subprocess; "
                "Path('src/mod.py').write_text('VALUE = 8\\n'); "
                "subprocess.run(['git','add','src/mod.py'],check=True); "
                "subprocess.run(['git','config','arb.task','mutated'],check=True); "
                "Path('.git/hooks/task-hook').write_text('mutated'); "
                "Path('.git/info/afrp-orchestrator.lock').write_text('unrelated')"
            ),
        ]
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "prohibited Git state" in (report.halted_reason or "")
        assert target.read_text(encoding="utf-8") == "VALUE = 7  # preexisting staged\n"
        restored_index = subprocess.run(
            ["git", "show", ":src/mod.py"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert restored_index == original_index
        config = subprocess.run(
            ["git", "config", "--get", "arb.task"],
            cwd=fixture_repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert config.returncode == 1
        assert not (fixture_repo / ".git" / "hooks" / "task-hook").exists()
        assert not (
            fixture_repo / ".git" / "info" / "afrp-orchestrator.lock"
        ).exists()

    def test_external_custom_index_is_restored_exactly(
        self, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        custom_index = fixture_repo / "custom-index"
        custom_index.write_bytes((fixture_repo / ".git" / "index").read_bytes())
        original = custom_index.read_bytes()
        monkeypatch.setenv("GIT_INDEX_FILE", str(custom_index))
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        command = [
            "python",
            "-c",
            (
                "from pathlib import Path; import subprocess; "
                "Path('src/mod.py').write_text('VALUE = 11\\n'); "
                "subprocess.run(['git','add','src/mod.py'],check=True)"
            ),
        ]
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "prohibited Git state" in (report.halted_reason or "")
        assert custom_index.read_bytes() == original

    def test_head_and_refs_mutation_is_prohibited_and_restored(
        self, fixture_repo: Path
    ) -> None:
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=fixture_repo, check=True, capture_output=True
        )
        git_dir = fixture_repo / ".git"

        def metadata_tree() -> tuple[dict[str, bytes], set[str]]:
            files = {
                path.relative_to(git_dir).as_posix(): path.read_bytes()
                for path in git_dir.rglob("*")
                if path.is_file()
                and path.name != "afrp-orchestrator.lock"
            }
            directories = {
                path.relative_to(git_dir).as_posix()
                for path in git_dir.rglob("*")
                if path.is_dir()
            }
            return files, directories

        original_metadata = metadata_tree()
        original_index_state = subprocess.run(
            ["git", "ls-files", "--stage", "-z"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
        ).stdout
        original_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        original_refs = subprocess.run(
            ["git", "show-ref"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        head_log_path = Path(
            subprocess.run(
                ["git", "rev-parse", "--git-path", "logs/HEAD"],
                cwd=fixture_repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        if not head_log_path.is_absolute():
            head_log_path = fixture_repo / head_log_path
        original_head_log = head_log_path.read_bytes()
        wp_path = fixture_repo / "05-work-packages" / "WP-TST-0001.yaml"
        command = [
            "python",
            "-c",
            (
                "from pathlib import Path; import subprocess; "
                "Path('src/mod.py').write_text('VALUE = 9\\n'); "
                "subprocess.run(['git','add','src/mod.py'],check=True); "
                "subprocess.run(['git','-c','user.email=t@t','-c','user.name=t',"
                "'commit','-q','-m','forbidden'],check=True); "
                "subprocess.run(['git','tag','task-created'],check=True); "
                "subprocess.run(['git','hash-object','-w','--stdin'],"
                "input=b'task-object',check=True); "
                "Path('.git/info/task-created').write_text('mutated')"
            ),
        ]
        wp_path.write_text(
            yaml.safe_dump(
                synthetic_wp('python -c "pass"', command), sort_keys=False
            ),
            encoding="utf-8",
        )
        report = orchestrate(fixture_repo, "WP-TST-0001")
        assert report.final_state is LifecycleState.HALTED
        assert "prohibited Git state" in (report.halted_reason or "")
        assert subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip() == original_head
        assert subprocess.run(
            ["git", "show-ref"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout == original_refs
        assert head_log_path.read_bytes() == original_head_log
        assert subprocess.run(
            ["git", "ls-files", "--stage", "-z"],
            cwd=fixture_repo,
            check=True,
            capture_output=True,
        ).stdout == original_index_state
        assert metadata_tree() == original_metadata
        assert (fixture_repo / "src" / "mod.py").read_text(encoding="utf-8") == "VALUE = 1\n"

    def test_existing_evidence_is_validated_without_overwrite(
        self, fixture_repo: Path
    ) -> None:
        first = orchestrate(fixture_repo, "WP-TST-0001")
        assert first.final_state is LifecycleState.REVIEW_PENDING, first.halted_reason
        target = (
            fixture_repo
            / "05-work-packages"
            / "WP-TST-0001"
            / "evidence"
            / "EXEC-900.yaml"
        )
        original = target.read_bytes()
        second = orchestrate(fixture_repo, "WP-TST-0001")
        assert second.final_state is LifecycleState.HALTED
        assert "validated existing evidence" in (second.halted_reason or "")
        assert target.read_bytes() == original

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
