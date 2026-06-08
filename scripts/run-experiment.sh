#!/bin/bash
# Run one or more Make targets and persist logs/metadata under results/runs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <make-target> [make-target...]" >&2
    exit 64
fi

RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
RESULTS_ROOT="${RESULTS_ROOT:-$PROJECT_ROOT/results/runs/$RUN_ID}"
mkdir -p "$RESULTS_ROOT"

json_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    s=${s//$'\n'/\\n}
    printf '%s' "$s"
}

run_target() {
    local target="$1"
    local target_dir="$RESULTS_ROOT/$target"
    local log_file="$target_dir/output.log"
    local meta_file="$target_dir/metadata.json"
    local start_epoch end_epoch exit_code git_commit started_at ended_at command

    mkdir -p "$target_dir"

    git_commit=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    start_epoch=$SECONDS
    command="make $target"

    echo "==> $command"
    set +e
    (
        cd "$PROJECT_ROOT"
        make "$target"
    ) 2>&1 | tee "$log_file"
    exit_code=${PIPESTATUS[0]}
    set -e

    end_epoch=$SECONDS
    ended_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    cat > "$meta_file" <<EOF
{
  "run_id": "$(json_escape "$RUN_ID")",
  "target": "$(json_escape "$target")",
  "command": "$(json_escape "$command")",
  "started_at": "$started_at",
  "ended_at": "$ended_at",
  "duration_sec": $((end_epoch - start_epoch)),
  "exit_code": $exit_code,
  "git_commit": "$(json_escape "$git_commit")",
  "log": "output.log"
}
EOF

    git -C "$PROJECT_ROOT" status --short > "$target_dir/git-status.txt" 2>/dev/null || true

    if [ "$exit_code" -ne 0 ]; then
        echo "Target '$target' failed with exit code $exit_code. Log: $log_file" >&2
        return "$exit_code"
    fi
}

overall=0
for target in "$@"; do
    if run_target "$target"; then
        :
    else
        overall=$?
        break
    fi
done

"$SCRIPT_DIR/summarize-results.sh" "$RESULTS_ROOT" >/dev/null || true
echo "Results: $RESULTS_ROOT"
exit "$overall"
