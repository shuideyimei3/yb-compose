#!/bin/bash
# Wait until YugabyteDB reports the expected number of visible nodes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/common.sh"

compose_cmd="${1:-docker compose -p yb-compose -f compose/base.yaml}"
host="${2:-yb-1}"
expected="${3:-5}"
timeout_s="${4:-240}"

cd "$PROJECT_ROOT"
wait_for_cluster "$compose_cmd" "$host" "$expected" "$timeout_s"
