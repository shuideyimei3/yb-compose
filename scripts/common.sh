#!/bin/bash

wait_for_cluster() {
    local compose_cmd="$1"
    local host="${2:-yb-1}"
    local expected="${3:-5}"
    local timeout_s="${4:-240}"
    local start count container_id
    local -a compose_args

    read -r -a compose_args <<< "$compose_cmd"
    start=$SECONDS
    while true; do
        container_id=$("${compose_args[@]}" ps -q "$host" 2>/dev/null | head -1 || true)
        if [ -n "$container_id" ]; then
            count=$(timeout 10s docker exec "$container_id" ysqlsh -h "$host" -tAc 'SELECT count(*) FROM yb_servers();' 2>/dev/null | tr -d '[:space:]' || true)
        else
            count=0
        fi
        if [[ "$count" =~ ^[0-9]+$ ]] && [ "$count" -ge "$expected" ]; then
            return 0
        fi

        if [ $((SECONDS - start)) -ge "$timeout_s" ]; then
            echo "Timed out waiting for YugabyteDB cluster (${count:-0}/${expected} nodes visible)" >&2
            return 1
        fi
        sleep 3
    done
}
