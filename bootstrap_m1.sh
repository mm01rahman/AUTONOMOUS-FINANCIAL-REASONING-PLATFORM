#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON=""
for candidate in python3 python; do
  if command -v "${candidate}" >/dev/null 2>&1 \
    && "${candidate}" -B -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'
  then
    PYTHON="${candidate}"
    break
  fi
done

if [[ -z "${PYTHON}" ]]; then
  echo "EOS-BOOT failed: Python 3.11+ is required." >&2
  exit 5
fi

export PYTHONPATH="${ROOT}/tools/afrp-cli${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON}" -B -m afrp.core.workspace --root "${ROOT}" "$@"
