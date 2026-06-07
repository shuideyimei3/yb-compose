# YugabyteDB 测评实验 Makefile
# =============================
# make up        - 启动基准集群 (RF=3, 无延迟)
# make up-delay  - 启动延迟环境 (NET_DELAY_MS=30)
# make status    - 查看集群状态
# make psql      - 连接 yb-1
# make bench     - 运行全部基准测试
# make bench-delay - 在延迟环境下运行基准测试
# make clean     - 关停并清理所有容器和数据

.PHONY: up up-delay status psql bench bench-delay clean

up:
	docker compose up -d --scale yb=3 --no-recreate
	docker compose wait rf3isready
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -c "SELECT host, cloud, region, zone FROM yb_servers() ORDER BY host;"

up-delay:
	docker compose --env-file=.env.delay up -d --scale yb=3 --no-recreate
	docker compose wait rf3isready
	@sleep 3
	@echo "=== 验证延迟注入 ==="
	docker compose exec yb-compose-yb-1 tc qdisc show dev eth0 2>/dev/null | grep -o 'delay [0-9]*ms' || echo "(tc not available)"
	docker compose exec yb-compose-yb-2 tc qdisc show dev eth0 2>/dev/null | grep -o 'delay [0-9]*ms' || true
	docker compose exec yb-compose-yb-3 tc qdisc show dev eth0 2>/dev/null | grep -o 'delay [0-9]*ms' || true

status:
	docker compose ps
	@echo ""
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -c "SELECT host, cloud, region, zone FROM yb_servers() ORDER BY host;"

psql:
	docker compose exec -it yb ysqlsh -h yb-compose-yb-1

# 构建压测工具镜像
build-bench:
	docker compose -f docker-compose.yaml -f docker-compose.bench.yaml build pg

bench: up
	@echo ">>> Phase 2.1: HLC 时钟"
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -f sql/01-hlc-clock.sql
	@echo ""
	@echo ">>> Phase 2.4: 表空间"
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -c "CREATE TABLESPACE region1 WITH ( replica_placement = '{\"num_replicas\": 1, \"placement_blocks\": [{\"cloud\": \"cloud\", \"region\": \"region1\", \"zone\": \"zone\", \"min_num_replicas\": 1}]}' );" 2>/dev/null || true
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -c "CREATE TABLESPACE region2 WITH ( replica_placement = '{\"num_replicas\": 1, \"placement_blocks\": [{\"cloud\": \"cloud\", \"region\": \"region2\", \"zone\": \"zone\", \"min_num_replicas\": 1}]}' );" 2>/dev/null || true
	docker compose exec -T yb ysqlsh -h yb-compose-yb-1 -c "CREATE TABLESPACE region3 WITH ( replica_placement = '{\"num_replicas\": 1, \"placement_blocks\": [{\"cloud\": \"cloud\", \"region\": \"region3\", \"zone\": \"zone\", \"min_num_replicas\": 1}]}' );" 2>/dev/null || true
	@echo "  Tablespaces created"
	@echo ""
	@echo ">>> Phase 3.1: perf_test + 延迟基准"
	bash scripts/01-setup-perf-test.sh
	python3 scripts/02-latency-bench.py --iter 30
	@echo ""
	@echo ">>> Phase 3.3: 一致性验证"
	bash scripts/03-consistency-test.sh
	@echo ""
	@echo ">>> Phase 4.3: 故障切换"
	bash scripts/04-failover-test.sh yb-compose-yb-1 yb-compose-yb-1

bench-delay: up-delay
	$(MAKE) bench

# 对基线环境和延迟环境分别做延迟测试对比
bench-compare: up
	@echo "=== 基线环境 (无延迟) ==="
	python3 scripts/02-latency-bench.py --iter 30
	@echo ""
	@echo "=== 切换到延迟环境 ==="
	docker compose down -v
	$(MAKE) up-delay
	python3 scripts/02-latency-bench.py --iter 30

clean:
	docker compose down -v 2>/dev/null || true
	docker rm -f yb-latency-client- 2>/dev/null || true
