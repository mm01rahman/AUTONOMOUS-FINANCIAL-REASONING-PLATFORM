"""AST invariant checker (WP-IMP-0005, FIT-002 / FIT-004).

Static checks over Python sources:

* **FIT-002** — bare ``except:`` handlers, ``except Exception`` handlers that
  swallow (no re-raise), and functions missing parameter/return annotations
  (EDR-004, EDR-11).
* **FIT-004 / EDR-002** — cross-layer imports inside the runtime package:
  ``afrp_runtime.layerN`` must never import a sibling ``afrp_runtime.layerM``,
  and ``afrp_runtime.common`` must not import any layer.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from afrp.core.exceptions import ContractReferenceError

_LAYER_PATTERN = re.compile(r"^afrp_runtime\.(layer[1-6]|common)(?:\.|$)")
_DUNDER_EXEMPT = frozenset({"__init__", "__new__", "__post_init__"})


@dataclass(frozen=True)
class Violation:
    """A single fitness-function violation found in a source file."""

    rule: str
    path: Path
    line: int
    message: str

    def render(self) -> str:
        """Render as ``RULE path:line message``."""
        return f"{self.rule} {self.path.as_posix()}:{self.line} {self.message}"


def _handler_reraises(handler: ast.ExceptHandler) -> bool:
    if not handler.body or not isinstance(handler.body[-1], ast.Raise):
        return False
    return _block_reaches_next(handler.body[:-1])


def _block_reaches_next(statements: list[ast.stmt]) -> bool:
    for statement in statements:
        if not _statement_reaches_next(statement):
            return False
    return True


def _statement_reaches_next(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.Return | ast.Raise | ast.Break | ast.Continue):
        return False
    if isinstance(statement, ast.If):
        if isinstance(statement.test, ast.Constant):
            selected = statement.body if statement.test.value else statement.orelse
            return _block_reaches_next(selected)
        return _block_reaches_next(statement.body) and _block_reaches_next(
            statement.orelse
        )
    if isinstance(statement, ast.While | ast.For | ast.AsyncFor):
        if (
            isinstance(statement, ast.While)
            and isinstance(statement.test, ast.Constant)
            and bool(statement.test.value)
        ):
            return False
        return _block_reaches_next(statement.body) and _block_reaches_next(
            statement.orelse
        )
    if isinstance(statement, ast.Try):
        if statement.finalbody and not _block_reaches_next(statement.finalbody):
            return False
        return (
            _block_reaches_next(statement.body)
            and _block_reaches_next(statement.orelse)
            and all(
                _block_reaches_next(handler.body) for handler in statement.handlers
            )
        )
    if isinstance(statement, ast.With | ast.AsyncWith):
        return _block_reaches_next(statement.body)
    if isinstance(statement, ast.Match):
        return all(_block_reaches_next(case.body) for case in statement.cases)
    return True


def _catches_generic_exception(node: ast.expr | None) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "Exception"
    if isinstance(node, ast.Attribute):
        return (
            isinstance(node.value, ast.Name)
            and node.value.id == "builtins"
            and node.attr == "Exception"
        )
    if isinstance(node, ast.Tuple):
        return any(_catches_generic_exception(element) for element in node.elts)
    return False


def _check_excepts(tree: ast.AST, path: Path) -> list[Violation]:
    findings: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            findings.append(
                Violation("FIT-002", path, node.lineno, "bare 'except:' handler (EDR-004)")
            )
        elif _catches_generic_exception(node.type) and not _handler_reraises(node):
            findings.append(
                Violation(
                    "FIT-002",
                    path,
                    node.lineno,
                    "'except Exception' without re-raise (EDR-004)",
                )
            )
    return findings


def _check_annotations(tree: ast.AST, path: Path) -> list[Violation]:
    findings: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        args = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        missing_params = [
            a.arg
            for a in args
            if a.annotation is None and a.arg not in ("self", "cls")
        ]
        if node.args.vararg is not None and node.args.vararg.annotation is None:
            missing_params.append("*" + node.args.vararg.arg)
        if node.args.kwarg is not None and node.args.kwarg.annotation is None:
            missing_params.append("**" + node.args.kwarg.arg)
        if missing_params:
            findings.append(
                Violation(
                    "FIT-002",
                    path,
                    node.lineno,
                    f"function '{node.name}' has unannotated parameters: "
                    f"{', '.join(missing_params)} (EDR-11)",
                )
            )
        if node.returns is None and node.name not in _DUNDER_EXEMPT:
            findings.append(
                Violation(
                    "FIT-002",
                    path,
                    node.lineno,
                    f"function '{node.name}' missing return annotation (EDR-11)",
                )
            )
    return findings


def _module_layer(path: Path) -> str | None:
    """Return 'layer1'..'layer6' or 'common' if ``path`` is inside afrp_runtime."""
    parts = path.parts
    if "afrp_runtime" not in parts:
        return None
    idx = parts.index("afrp_runtime")
    if idx + 1 >= len(parts) - 1:  # afrp_runtime/<module>.py has no layer dir
        return None
    candidate = parts[idx + 1]
    if re.fullmatch(r"layer[1-6]|common", candidate):
        return candidate
    return None


def _resolve_relative_import(node: ast.ImportFrom, path: Path) -> list[str]:
    parts = path.parts
    runtime_index = parts.index("afrp_runtime")
    package = list(parts[runtime_index + 1 : -1])
    levels_up = node.level - 1
    if levels_up > len(package):
        return []
    prefix = package[: len(package) - levels_up]
    if node.module:
        return ["afrp_runtime." + ".".join([*prefix, *node.module.split(".")])]
    return [
        "afrp_runtime." + ".".join([*prefix, alias.name])
        for alias in node.names
        if alias.name != "*"
    ]


def _imported_modules(tree: ast.AST, path: Path) -> list[tuple[str, int]]:
    modules: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.append((node.module, node.lineno))
            elif node.level > 0:
                modules.extend(
                    (module, node.lineno)
                    for module in _resolve_relative_import(node, path)
                )
    return modules


def _check_cross_layer(tree: ast.AST, path: Path) -> list[Violation]:
    own = _module_layer(path)
    if own is None:
        return []
    findings: list[Violation] = []
    for module, line in _imported_modules(tree, path):
        match = _LAYER_PATTERN.match(module)
        if not match:
            continue
        target = match.group(1)
        if target == own:
            continue
        if own == "common":
            findings.append(
                Violation(
                    "FIT-004",
                    path,
                    line,
                    f"common must not import layer package '{module}' (EDR-002)",
                )
            )
        elif target != "common":
            findings.append(
                Violation(
                    "FIT-004",
                    path,
                    line,
                    f"layer '{own}' must not import sibling '{module}' (EDR-002)",
                )
            )
    return findings


def check_source(source: str, path: Path) -> list[Violation]:
    """Run all AST checks against ``source`` attributed to ``path``.

    Raises:
        SyntaxError: the source is not valid Python.
    """
    tree = ast.parse(source, filename=str(path))
    findings = [
        *_check_excepts(tree, path),
        *_check_annotations(tree, path),
        *_check_cross_layer(tree, path),
    ]
    return sorted(findings, key=lambda v: (v.path.as_posix(), v.line, v.rule))


def scan_paths(roots: list[Path]) -> list[Violation]:
    """Scan every ``*.py`` file under each required root."""
    findings: list[Violation] = []
    for root in roots:
        if not root.exists():
            raise ContractReferenceError(str(root))
        for file in sorted(root.rglob("*.py")):
            # utf-8-sig mirrors CPython's own BOM tolerance for source files.
            source = file.read_text(encoding="utf-8-sig")
            findings.extend(check_source(source, file))
    return findings
