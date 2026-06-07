-- Phase 2.1 - HLC 时钟同步实验
-- 观察 YugabyteDB Hybrid Logical Clock 的行为

-- 创建测试表
CREATE TABLE IF NOT EXISTS test_clock (id INT PRIMARY KEY, ts TEXT);

-- 写入并观察 hybrid time (HLC -> physical + logical)
INSERT INTO test_clock VALUES (1, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS.US'));

-- 读取
SELECT * FROM test_clock;

-- 对比不同节点上的 now() 差异 - 观察 clock_drift
SELECT host, now()::timestamptz(6) AS current_time
FROM yb_servers()
ORDER BY host;
