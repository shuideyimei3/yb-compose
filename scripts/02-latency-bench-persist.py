#!/usr/bin/env python3
"""
Phase 3.1 - 延迟对比实验 (持久连接版)
使用持久 psql 进程消除每查询连接开销，测量真实查询延迟。

用法:
  ./scripts/02-latency-bench-persist.py [--hosts yb-1,yb-2] [--iter 50]
"""
import subprocess, random, time, sys, argparse, json, os

CLIENT_IMAGE = "alpine:latest"
CLIENT_NAME = f"yb-latency-persist-{os.getpid()}"

def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)

def start_client():
    run(["docker", "run", "-d", "--name", CLIENT_NAME,
         "--network", "yb-compose_default", CLIENT_IMAGE, "sleep", "3600"],
        timeout=30)
    run(["docker", "exec", CLIENT_NAME, "apk", "add", "--no-cache",
         "postgresql-client"], timeout=60)

def stop_client():
    run(["docker", "rm", "-f", CLIENT_NAME], timeout=10)

class PsqlConnection:
    """Persistent psql subprocess: send SQL via stdin, read result from stdout."""

    def __init__(self, client_name, host):
        self.host = host
        self.proc = subprocess.Popen(
            ["docker", "exec", "-i", client_name, "psql",
             "-h", host, "-U", "yugabyte", "-tAc"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # Drain any startup banners by reading the initial prompt line
        # psql with -tAc shouldn't produce extra output, but give it a moment
        self._read_ready()

    def _read_ready(self):
        """Send a no-op query to verify the connection is alive."""
        self.proc.stdin.write("SELECT 1;\n")
        self.proc.stdin.flush()
        # Read until we get the result line
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(f"psql process died for host {self.host}")
            stripped = line.strip()
            if stripped:
                break

    def execute(self, sql):
        """Send SQL, return (output_text, latency_ns)."""
        t0 = time.time_ns()
        self.proc.stdin.write(sql + "\n")
        self.proc.stdin.flush()
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(f"psql process died for host {self.host}")
            stripped = line.strip()
            if stripped == "":
                # Empty line after result — psql -A outputs result then blank line
                if lines:
                    break
                continue
            lines.append(stripped)
        t1 = time.time_ns()
        return "\n".join(lines), (t1 - t0) / 1_000_000

    def close(self):
        try:
            self.proc.stdin.write("\\q\n")
            self.proc.stdin.flush()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()

def measure(conn, op, n):
    """Measure n iterations of read or write on a persistent connection."""
    results = []
    for _ in range(n):
        if op == "read":
            rid = random.randint(1, 10000)
            sql = f"SELECT * FROM perf_test WHERE id = {rid};"
        else:
            sql = "INSERT INTO perf_test (data) VALUES (repeat('x', 256)) RETURNING id;"
        _, latency_ms = conn.execute(sql)
        results.append(latency_ms)
    results.sort()
    avg = sum(results) / len(results)
    p50 = results[len(results) // 2]
    p99 = results[int(len(results) * 0.99)]
    return {"avg_ms": round(avg, 2), "p50_ms": round(p50, 2), "p99_ms": round(p99, 2)}

def main():
    parser = argparse.ArgumentParser(description="YB latency benchmark (persistent connections)")
    parser.add_argument("--hosts", type=str, default="yb-1,yb-2,yb-3,yb-4,yb-5",
                        help="comma-separated host list")
    parser.add_argument("--iter", type=int, default=50, help="iterations per test")
    args = parser.parse_args()

    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]
    host_labels = {}
    for h in hosts:
        # Try to infer label from host name
        num = h.rsplit("-", 1)[-1] if "-" in h else h
        delay_map = {"1": 30, "2": 60, "3": 90, "4": 120, "5": 150}
        delay = delay_map.get(num, "?")
        host_labels[h] = f"region{num} ({delay}ms egress)"

    print(f"Starting latency benchmark (persistent connections, {args.iter} iterations per test)...")
    start_client()

    try:
        # Verify row count
        tmp_conn = PsqlConnection(CLIENT_NAME, hosts[0])
        output, _ = tmp_conn.execute("SELECT count(*) FROM perf_test;")
        tmp_conn.close()
        row_count = int(output.strip()) if output.strip().isdigit() else 0
        print(f"perf_test row count: {row_count}")
        if row_count == 0:
            print("WARNING: perf_test table is empty. Run scripts/01-setup-perf-test.sh first.")

        # Print header
        print(f"\n{'Host':<30} {'Op':<8} {'Avg (ms)':>10} {'P50 (ms)':>10} {'P99 (ms)':>10}")
        print("-" * 72)

        all_results = {}
        for host in hosts:
            label = host_labels.get(host, host)
            conn = PsqlConnection(CLIENT_NAME, host)
            try:
                for op in ["read", "write"]:
                    r = measure(conn, op, args.iter)
                    print(f"{label:<30} {op.upper():<8} {r['avg_ms']:>10} {r['p50_ms']:>10} {r['p99_ms']:>10}")
                    all_results[f"{host}_{op}"] = r
            finally:
                conn.close()

        # Output JSON
        print("\n=== JSON ===")
        print(json.dumps(all_results, indent=2))
    finally:
        stop_client()

if __name__ == "__main__":
    main()
