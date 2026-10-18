#!/bin/sh
set -eu
HARNESS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HARNESS_DIR"
exec python3 scripts/open_demo.py "$@"
