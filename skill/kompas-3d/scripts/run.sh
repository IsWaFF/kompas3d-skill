#!/usr/bin/env bash
# Linux shortcut for run.py (see it for the env variables): run.sh script.py [args...]
exec python3 "$(dirname "$0")/run.py" "$@"
