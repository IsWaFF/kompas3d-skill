#!/usr/bin/env bash
# Run a Python script against the running KOMPAS-3D inside the distrobox.
# Usage: run.sh script.py [args...]
# Env:   T=seconds (timeout, default 120), KOMPAS_BOX (default kompas-box),
#        KOMPAS_DIR (default /opt/ascon/kompas3d-v25).
# The script can `import ksapi`, `from constants import constants as c`
# and `import ks` (helpers from this skill).
set -euo pipefail

[[ $# -ge 1 ]] || { echo "usage: $0 script.py [args...]" >&2; exit 2; }
SKILL_DIR=$(cd "$(dirname "$0")" && pwd)
BOX=${KOMPAS_BOX:-kompas-box}
BIN=${KOMPAS_DIR:-/opt/ascon/kompas3d-v25}/Bin
script=$(realpath "$1"); shift

# ksapi expects to be imported from the KOMPAS Bin directory, so cd there.
# The box prints apport noise on every start; filter it out.
# shellcheck disable=SC2016  # $0/$1/$@ belong to the inner bash
distrobox enter "$BOX" -- env PYTHONPATH="$BIN:$SKILL_DIR" \
  bash -c 'cd "$1" && shift && exec timeout "$0" python3 "$@"' "${T:-120}" "$BIN" "$script" "$@" 2>&1 \
  | { grep -v -i apport || true; }
