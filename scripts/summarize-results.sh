#!/bin/bash
# Generate a Markdown summary for a results/runs/<run_id> directory.
set -euo pipefail

RUN_DIR="${1:-}"
if [ -z "$RUN_DIR" ]; then
    echo "Usage: $0 <results-run-dir>" >&2
    exit 64
fi

if [ ! -d "$RUN_DIR" ]; then
    echo "Run directory not found: $RUN_DIR" >&2
    exit 66
fi

summary="$RUN_DIR/summary.md"
run_id="$(basename "$RUN_DIR")"

extract_json_string() {
    local key="$1" file="$2"
    sed -nE "s/^[[:space:]]*\"$key\"[[:space:]]*:[[:space:]]*\"(.*)\"[,]?$/\1/p" "$file" | head -1
}

extract_json_number() {
    local key="$1" file="$2"
    sed -nE "s/^[[:space:]]*\"$key\"[[:space:]]*:[[:space:]]*([0-9]+)[,]?$/\1/p" "$file" | head -1
}

md_cell_escape() {
    local s="$1"
    s=${s//\\/\\\\}
    s=${s//|/\\|}
    printf '%s' "$s"
}

strip_ansi() {
    sed -E 's/\x1B\[[0-9;]*[[:alpha:]]//g'
}

{
    echo "# Experiment Run Summary"
    echo ""
    echo "- Run ID: \`$run_id\`"
    echo "- Generated at: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
    echo ""
    echo "| Target | Status | Duration | Key Metrics | Log |"
    echo "|---|---:|---:|---|---|"

    while IFS= read -r meta; do
        target="$(extract_json_string target "$meta")"
        exit_code="$(extract_json_number exit_code "$meta")"
        duration="$(extract_json_number duration_sec "$meta")"
        target_dir="$(dirname "$meta")"
        log_file="$target_dir/output.log"
        log_rel="${target_dir#$RUN_DIR/}/output.log"
        status="PASS"
        [ "$exit_code" != "0" ] && status="FAIL($exit_code)"

        metrics=""
        if [ -f "$log_file" ]; then
            case "$target" in
                experiment-02|experiment-03)
                    metrics="$(grep -E '║  yb-[1-5][[:space:]]+│' "$log_file" | strip_ansi | sed 's/[[:space:]]\+/ /g' | tr '\n' '; ' | sed 's/; $//')"
                    ;;
                experiment-04)
                    metrics="$(grep -E 'docker stop|iptables 分区' "$log_file" | strip_ansi | sed 's/[[:space:]]\+/ /g' | tr '\n' '; ' | sed 's/; $//')"
                    ;;
                experiment-10)
                    metrics="$(grep -E 'tpmC=|tpmC:' "$log_file" | tail -1 | strip_ansi | sed 's/[[:space:]]\+/ /g')"
                    ;;
                experiment-11)
                    metrics="$(grep -E 'N=[0-9]+: TPS' "$log_file" | strip_ansi | sed 's/[[:space:]]\+/ /g' | tr '\n' '; ' | sed 's/; $//')"
                    ;;
            esac
        fi
        [ -z "$metrics" ] && metrics="-"
        metrics="$(md_cell_escape "$metrics")"

        echo "| \`$target\` | $status | ${duration}s | $metrics | [$log_rel]($log_rel) |"
    done < <(find "$RUN_DIR" -mindepth 2 -maxdepth 2 -name metadata.json | sort)
} > "$summary"

echo "$summary"
