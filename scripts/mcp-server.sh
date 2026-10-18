#!/bin/sh
set -eu
HARNESS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$HARNESS_DIR"
exec "${FINANCIAL_HARNESS_PYTHON:-python3}" -m harness --workspace "${FINANCIAL_HARNESS_WORKSPACE:-$HARNESS_DIR/workspace}" mcp
