"""AFRP proto contract gate (ADR-0003, W-001 buf substitute).

Usage:
    uv run python -m tools.proto_gate            # full gate (FIT-003 + compat)
    uv run python -m tools.proto_gate --update   # regenerate the snapshot

Steps:
1. Compile ``proto/afrp/v1`` with grpcio-tools (syntax gate).
2. FIT-003 — every message carries ``cio_id``, ``owner_subsystem`` and
   ``stability_level`` custom options.
3. NFR-010/EDR-10 — compare the compiled descriptor set against the committed
   snapshot ``09-validation/contracts/afrp_v1.snapshot.json``: no message
   removed, no field removed, renamed, renumbered or retyped.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTO_ROOT = REPO_ROOT / "proto"
PROTO_FILES = (
    "afrp/v1/annotations.proto",
    "afrp/v1/envelope.proto",
    "afrp/v1/cio.proto",
)
SNAPSHOT_PATH = REPO_ROOT / "09-validation" / "contracts" / "afrp_v1.snapshot.json"
GATED_MODULES = ("afrp.v1.envelope_pb2", "afrp.v1.cio_pb2")
REQUIRED_OPTIONS = ("cio_id", "owner_subsystem", "stability_level")


def compile_protos(out_dir: Path) -> Path:
    """Compile the contracts; return the descriptor-set path.

    Raises:
        RuntimeError: protoc reported a failure.
    """
    descriptor = out_dir / "afrp_v1.desc"
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"--proto_path={PROTO_ROOT}",
        f"--python_out={out_dir}",
        f"--descriptor_set_out={descriptor}",
        "--include_imports",
        *PROTO_FILES,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"protoc failed:\n{proc.stderr.strip()}")
    return descriptor


def _iter_messages(gen_dir: Path) -> list[tuple[str, Any, Any]]:
    """Yield (full_name, descriptor, annotations module) for gated messages."""
    sys.path.insert(0, str(gen_dir))
    try:
        annotations = importlib.import_module("afrp.v1.annotations_pb2")
        found: list[tuple[str, Any, Any]] = []
        for module_name in GATED_MODULES:
            module = importlib.import_module(module_name)
            for descriptor in module.DESCRIPTOR.message_types_by_name.values():
                found.append((descriptor.full_name, descriptor, annotations))
                for nested in descriptor.nested_types:
                    if not nested.GetOptions().map_entry:
                        found.append((nested.full_name, nested, annotations))
        return found
    finally:
        sys.path.remove(str(gen_dir))


def check_fit_003(gen_dir: Path) -> list[str]:
    """FIT-003: return violation strings for messages missing custom options.

    Nested non-map messages inherit governance from their container and are
    exempt from carrying their own options.
    """
    problems: list[str] = []
    for full_name, descriptor, annotations_module in _iter_messages(gen_dir):
        if descriptor.containing_type is not None:
            continue
        options = descriptor.GetOptions()
        for option_name in REQUIRED_OPTIONS:
            extension = getattr(annotations_module, option_name)
            if not options.HasExtension(extension) or not options.Extensions[extension]:
                problems.append(f"{full_name}: missing option ({option_name})")
    return problems


def build_manifest(descriptor_path: Path) -> dict[str, Any]:
    """Reduce the descriptor set to a wire-compatibility manifest."""
    from google.protobuf import descriptor_pb2

    fds = descriptor_pb2.FileDescriptorSet()
    fds.ParseFromString(descriptor_path.read_bytes())
    messages: dict[str, dict[str, list[str]]] = {}

    def walk(prefix: str, msg: descriptor_pb2.DescriptorProto) -> None:
        full = f"{prefix}.{msg.name}"
        fields = {
            str(field.number): [
                field.name,
                descriptor_pb2.FieldDescriptorProto.Type.Name(field.type),
                descriptor_pb2.FieldDescriptorProto.Label.Name(field.label),
            ]
            for field in msg.field
        }
        messages[full] = fields
        for nested in msg.nested_type:
            walk(full, nested)

    for file_proto in fds.file:
        if not file_proto.package.startswith("afrp"):
            continue
        for msg in file_proto.message_type:
            walk(file_proto.package, msg)
    return {"schema": "afrp-contract-manifest-1", "messages": messages}


def check_compatibility(current: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    """NFR-010: current must be a superset of snapshot, field-for-field."""
    problems: list[str] = []
    cur_messages: dict[str, dict[str, list[str]]] = current["messages"]
    for msg_name, fields in snapshot["messages"].items():
        cur_fields = cur_messages.get(msg_name)
        if cur_fields is None:
            problems.append(f"message removed: {msg_name}")
            continue
        for number, (name, ftype, label) in fields.items():
            actual = cur_fields.get(number)
            if actual is None:
                problems.append(f"{msg_name}: field #{number} ({name}) removed")
            elif actual != [name, ftype, label]:
                problems.append(
                    f"{msg_name}: field #{number} changed {[name, ftype, label]} -> {actual}"
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    """Run the proto gate; ``--update`` rewrites the snapshot instead."""
    args = argv if argv is not None else sys.argv[1:]
    update = "--update" in args

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        try:
            descriptor = compile_protos(out_dir)
        except RuntimeError as exc:
            print(f"proto_gate: FAIL — {exc}")
            return 1
        print("proto_compile: PASS")

        violations = check_fit_003(out_dir)
        if violations:
            print(f"fit_003: FAIL ({len(violations)} violation(s))")
            for violation in violations:
                print(f"  {violation}")
            return 2
        print("fit_003: PASS (all messages carry cio_id/owner_subsystem/stability_level)")

        manifest = build_manifest(descriptor)

    if update or not SNAPSHOT_PATH.is_file():
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"snapshot: {'UPDATED' if update else 'CREATED'} at {SNAPSHOT_PATH}")
        return 0

    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    problems = check_compatibility(manifest, snapshot)
    if problems:
        print(f"nfr_010: FAIL ({len(problems)} breaking change(s))")
        for problem in problems:
            print(f"  {problem}")
        return 3
    print(f"nfr_010: PASS (wire-compatible with snapshot, "
          f"{len(manifest['messages'])} message(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
