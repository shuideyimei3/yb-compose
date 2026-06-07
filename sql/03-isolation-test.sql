-- Phase 2.3 - 隔离级别与冲突事务测试

-- 验证隔离级别
SHOW default_transaction_isolation;

-- 测试 Read Committed 下的冲突事务
-- 需要在两个独立的 session 中运行

-- Session 1:
BEGIN ISOLATION LEVEL READ COMMITTED;
UPDATE test_clock SET ts = to_char(now(), 'YYYY-MM-DD HH24:MI:SS.US') WHERE id = 1;
-- 此时不提交，Session 2 的 UPDATE 会被阻塞
SELECT pg_sleep(3);
COMMIT;

-- Session 2 (在另一个连接中运行):
BEGIN ISOLATION LEVEL READ COMMITTED;
UPDATE test_clock SET ts = to_char(now(), 'YYYY-MM-DD HH24:MI:SS.US') WHERE id = 1;
-- 如果 Session 1 未提交，此 UPDATE 会等待行锁
-- Session 1 提交后，此 UPDATE 继续执行
COMMIT;
