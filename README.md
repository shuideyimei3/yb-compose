# yblab — YugabyteDB 全球分布式数据库测评

在单机 Docker 上搭建 3 节点 RF=3 的 YugabyteDB 集群，通过 tc netem 模拟跨 region 网络延迟，完成完整的分布式数据库测评实验。

## 仓库结构

```
.
├── docker-compose.yaml          # 集群定义 (3 yb + pg + rf3isready)
├── docker-compose.bench.yaml    # 压测工具镜像构建
├── Dockerfile.pg                # 自定义 pg 镜像 (预装 pgbench)
├── Makefile                     # 一键实验入口
├── .env                         # 基准环境配置 (NET_DELAY_MS=1)
├── .env.delay                   # 延迟环境配置 (NET_DELAY_MS=30)
├── README.md
├── 执行计划-YugabyteDB.md        # 完整实验计划
├── 实验结果汇总.md               # 实验结果
├── scripts/
│   ├── 01-setup-perf-test.sh    # 创建 perf_test 表并填充
│   ├── 02-latency-bench.py      # 跨节点延迟基准测试
│   ├── 03-consistency-test.sh   # 一致性级别 + 转账正确性
│   ├── 04-failover-test.sh      # 故障切换 RTO/RPO
│   └── run-all.sh               # 全自动实验脚本
└── sql/
    ├── 01-hlc-clock.sql         # HLC 时钟同步实验
    ├── 02-tablespaces.sql       # Geo-Partitioning 表空间
    └── 03-isolation-test.sql    # 隔离级别测试
```

## 所需 Docker 镜像

| 镜像 | 用途 | 来源 |
|------|------|------|
| `yugabytedb/yugabyte` | YugabyteDB 数据库节点 | Docker Hub (自动拉取) |
| `postgres:16` | 客户端工具 (psql, pgbench) | Docker Hub (自动拉取) |
| `caddy:2-alpine` | Web UI 反向代理 | Docker Hub (自动拉取) |
| `alpine:latest` | 轻量级网络测试容器 | Docker Hub (自动拉取) |

所有镜像均在 `docker-compose.yaml` 中定义，首次启动时自动拉取。

## 快速开始

```bash
# 1. 启动基准集群 (3 节点, 无延迟)
make up

# 2. 或启动延迟环境 (region1=30ms, region2=60ms, region3=90ms)
make up-delay

# 3. 连接数据库
make psql

# 4. 运行全部实验
make bench

# 5. 在延迟环境下跑实验
make bench-delay

# 6. 关停清理
make clean
```

## 实验内容

### Phase 1: 环境搭建与验证
- 启动 3 节点 RF=3 集群
- 验证拓扑 (cloud.region{1..3}.zone)
- 验证复制因子 (RF=3)
- 验证延迟注入 (tc netem)

### Phase 2: 架构分析
- **HLC 时钟同步**: 对比各节点 `now()`
- **Raft 共识**: 查看 tablet leader/follower 分布
- **隔离级别**: 验证 Read Committed + 冲突事务
- **Geo-Partitioning**: 创建 region 表空间 + Leader Preference

### Phase 3: 基准测试
- **延迟对比**: 测量 3 个节点的读写延迟 (avg/P50/P99)
- **一致性**: 测试 leader_only / follower_read
- **正确性**: 并发转账 + 余额守恒验证

### Phase 4: 进阶实验
- **故障切换**: 停节点 → 测量 RTO/RPO

## 延迟模拟原理

```yaml
# docker-compose.yaml 关键部分:
cap_add:
  - NET_ADMIN  # 允许修改网络队列

# 启动时注入 tc netem:
# NET_DELAY_MS=30, zone编号=1/2/3
# region1: tc qdisc add dev eth0 root netem delay 30ms
# region2: tc qdisc add dev eth0 root netem delay 60ms  
# region3: tc qdisc add dev eth0 root netem delay 90ms
```

各节点 egress 延迟通过 `tc netem` 注入，影响容器间出站流量。跨节点 RTT = 源节点 egress + 目标节点 egress。

## 网络延迟对比

| 环境 | 配置 | 节点延迟 | 读 avg | 读 P50 | 写 avg |
|------|------|---------|--------|--------|--------|
| 基准 | NET_DELAY_MS=1 | ~0ms | 41ms | 40ms | 41ms |
| 延迟 | NET_DELAY_MS=30 | 30/60/90ms | 93-169ms | 89-166ms | 91-178ms |
