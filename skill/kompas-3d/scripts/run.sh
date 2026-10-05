#!/bin/bash
# Run a Python script against the running KOMPAS-3D (inside distrobox kompas-box).
# Usage: run.sh /abs/path/script.py   (T=seconds overrides the 120s timeout)
# The script can `import ksapi`, `from constants import constants as c`,
# and `import ks` (helpers from this skill).
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
exec distrobox enter kompas-box -- bash -c \
  "cd /opt/ascon/kompas3d-v25/Bin && PYTHONPATH=/opt/ascon/kompas3d-v25/Bin:$SKILL_DIR timeout ${T:-120} python3 $* 2>&1 | grep -v -i apport"
