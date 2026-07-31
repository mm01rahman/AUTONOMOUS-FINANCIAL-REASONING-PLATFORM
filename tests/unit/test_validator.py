"""Unit tests for WP-IMP-0005: afrp validate and the AST invariant checker."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from afrp.cli import cli
from afrp.core.astcheck import Violation, check_source, scan_paths
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = Path("mod.py")


def check(code: str, path: Path = SRC) -> list[Violation]:
    return check_source(textwrap.dedent(code), path)


class TestFit002Excepts:
    def test_bare_except_flagged(self) -> None:
        findings = check(
            """
            def f() -> None:
                try:
                    pass
                except:
                    pass
            """
        )
        assert any("bare 'except:'" in v.message for v in findings)

    def test_swallowed_exception_flagged(self) -> None:
        findings = check(
            """
            def f() -> None:
                try:
                    pass
                except Exception:
                    pass
            """
        )
        assert any("without re-raise" in v.message for v in findings)

    def test_reraised_exception_allowed(self) -> None:
        findings = check(
            """
            def f() -> None:
                try:
                    pass
                except Exception as exc:
                    raise RuntimeError("wrapped") from exc
            """
        )
        assert not [v for v in findings if "re-raise" in v.message]

    def test_typed_except_allowed(self) -> None:
        findings = check(
            """
            def f() -> None:
                try:
                    pass
                except ValueError:
                    pass
            """
        )
        assert findings == []


class TestFit002Annotations:
    def test_unannotated_params_flagged(self) -> None:
        findings = check("def f(a, b) -> None: ...\n")
        assert any("unannotated parameters: a, b" in v.message for v in findings)

    def test_missing_return_flagged(self) -> None:
        findings = check("def f(a: int): ...\n")
        assert any("missing return annotation" in v.message for v in findings)

    def test_self_and_cls_exempt(self) -> None:
        findings = check(
            """
            class C:
                def m(self, x: int) -> int:
                    return x
                @classmethod
                def n(cls) -> None: ...
            """
        )
        assert findings == []

    def test_dunder_init_return_exempt(self) -> None:
        findings = check(
            """
            class C:
                def __init__(self, x: int):
                    self.x = x
            """
        )
        assert findings == []

    def test_varargs_annotations_required(self) -> None:
        findings = check("def f(*args, **kwargs) -> None: ...\n")
        assert any("*args" in v.message and "**kwargs" in v.message for v in findings)

    def test_async_functions_checked(self) -> None:
        findings = check("async def f(a): ...\n")
        assert len(findings) == 2  # params + return


class TestFit004CrossLayer:
    def test_sibling_layer_import_flagged(self) -> None:
        path = Path("06-runtime") / "afrp_runtime" / "layer2" / "agent.py"
        findings = check("import afrp_runtime.layer3.sim\n", path)
        assert any(v.rule == "FIT-004" for v in findings)

    def test_from_import_sibling_flagged(self) -> None:
        path = Path("06-runtime") / "afrp_runtime" / "layer4" / "policy.py"
        findings = check("from afrp_runtime.layer5.gateway import send\n", path)
        assert any("must not import sibling" in v.message for v in findings)

    def test_common_import_allowed_from_layer(self) -> None:
        path = Path("06-runtime") / "afrp_runtime" / "layer4" / "policy.py"
        findings = check("from afrp_runtime.common.config import load\n", path)
        assert findings == []

    def test_own_layer_import_allowed(self) -> None:
        path = Path("06-runtime") / "afrp_runtime" / "layer2" / "agent.py"
        findings = check("from afrp_runtime.layer2.base import BaseAgent\n", path)
        assert findings == []

    def test_common_importing_layer_flagged(self) -> None:
        path = Path("06-runtime") / "afrp_runtime" / "common" / "util.py"
        findings = check("import afrp_runtime.layer1.ingest\n", path)
        assert any("common must not import layer" in v.message for v in findings)

    def test_outside_runtime_not_checked(self) -> None:
        findings = check("import afrp_runtime.layer1.ingest\n", Path("tools") / "x.py")
        assert findings == []


class TestScanPaths:
    def test_scan_flags_violations_in_tree(self, tmp_path: Path) -> None:
        bad = tmp_path / "pkg"
        bad.mkdir()
        (bad / "bad.py").write_text("def f(a):\n    pass\n", encoding="utf-8")
        findings = scan_paths([tmp_path])
        assert findings
        assert all(v.rule == "FIT-002" for v in findings)

    def test_scan_ignores_missing_roots(self, tmp_path: Path) -> None:
        assert scan_paths([tmp_path / "ghost"]) == []

    def test_syntax_error_propagates(self, tmp_path: Path) -> None:
        (tmp_path / "broken.py").write_text("def (:\n", encoding="utf-8")
        with pytest.raises(SyntaxError):
            scan_paths([tmp_path])

    def test_repository_sources_are_clean(self) -> None:
        roots = [
            REPO_ROOT / "tools" / "afrp-cli",
            REPO_ROOT / "06-runtime",
            REPO_ROOT / "tests",
        ]
        assert scan_paths(roots) == []


class TestValidateCommand:
    def test_validate_passes_on_real_repository(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["validate", "--repo-root", str(REPO_ROOT)])
        assert outcome.exit_code == 0, outcome.output
        assert "fit_002: PASS" in outcome.output
        assert "fit_004: PASS" in outcome.output
        assert "fit_006: PASS" in outcome.output

    def test_validate_fails_with_violations(self, tmp_path: Path) -> None:
        gov = tmp_path / "00-governance"
        gov.mkdir()
        (gov / "KERNEL.md").write_text("# K\nsmall kernel\n", encoding="utf-8")
        src = tmp_path / "tests"
        src.mkdir()
        (src / "bad.py").write_text(
            "def f():\n    try:\n        pass\n    except:\n        pass\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        outcome = runner.invoke(cli, ["validate", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 3
        assert "FIT-002" in outcome.output

    def test_validate_halts_without_kernel(self, tmp_path: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["validate", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output
