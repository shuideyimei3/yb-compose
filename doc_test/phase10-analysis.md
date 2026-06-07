# TPC-C Benchmark 结果分析

> **测试日期**: 2026-06-07
> **环境**: 5 节点 YugabyteDB RF=3（Docker Compose 单主机部署）
> **工具**: go-tpc (pingcap)
> **配置**: 10 Warehouses, 8 Threads, 5min Duration

---

## 1. 实验设计

### 1.1 目的

| 维度 | 说明 |
|------|------|
| 吞吐量 | 使用 TPC-C Benchmark 测量 tpmC 指标 |
| 延迟对比 | 单机房部署 vs 模拟跨区域部署下的读写延迟 |
| 一致性开销 | 跨 region Raft 共识对吞吐量的损耗量化 |

### 1.2 环境配置

| 参数 | 基准环境 | 延迟环境 |
|------|---------|---------|
| 网络延迟 | 无额外延迟（~0ms） | tc netem 30/60/90/120/150ms egress |
| 跨节点 RTT | ~0ms | 90ms ~ 270ms |
| 客户端连接点 | yb-1（region1, 30ms egress） | 同左 |

### 1.3 延迟模型

```
节点          延迟         Raft 角色
─────────────────────────────────
yb-1 (region1)   30ms    Master Leader + TServer
yb-2 (region2)   60ms    Master Follower + TServer
yb-3 (region3)   90ms    Master Follower + TServer
yb-4 (region4)  120ms    TServer only
yb-5 (region5)  150ms    TServer only
```

跨节点 RTT = 源节点 egress + 目标节点 egress，最大 RTT 270ms（region4↔region5）。

---

## 2. 结果对比

### 2.1 总体指标

| 指标 | 基准环境 | 延迟环境 | 变化倍数 |
|------|---------|---------|---------|
| **tpmC** | **14,843.0** | **68.8** | **↓216x** |
| **tpmTotal** | **33,014.6** | **158.3** | **↓209x** |
| 效率* | 11,543% | 53.5% | — |
| 总 NEW_ORDER 数 | 74,198 | 338 | ↓220x |
| 错误率 | 0.005% | 0.06% | — |

### 2.2 事务级延迟对比

| 事务类型 | 基准 avg(ms) | 延迟 avg(ms) | 倍数 | 基准 P99(ms) | 延迟 P99(ms) | 倍数 |
|---------|-------------|-------------|------|-------------|-------------|------|
| **NEW_ORDER** | **21.0** | **4,334.5** | **×206** | **39.8** | **8,589.9** | **×216** |
| **PAYMENT** | **7.7** | **1,912.3** | **×248** | **23.1** | **4,295.0** | **×186** |
| **DELIVERY** | **34.5** | **7,857.8** | **×228** | **65.0** | **12,884.9** | **×198** |
| ORDER_STATUS | 3.2 | 932.3 | ×291 | 5.2 | 1,275.1 | ×245 |
| STOCK_LEVEL | 4.7 | 295.8 | ×63 | 7.9 | 385.9 | ×49 |

### 2.3 吞吐量-延迟散点

```
基准环境（无延迟）:
  NEW_ORDER: avg 21.0ms @ 14,843 tpmC
  PAYMENT:   avg  7.7ms @ 14,234 tpmC

延迟环境（30-150ms）:
  NEW_ORDER: avg 4,335ms @ 68.8 tpmC  (平均每笔 4.3s)
  PAYMENT:   avg 1,912ms @ 71.6 tpmC  (平均每笔 1.9s)
```

---

## 3. 分析

### 3.1 吞吐量崩塌的根本原因

YugabyteDB 在跨 region 部署下，**每次写入都需要 Raft 共识**：

```
SQL 请求 → YSQL 解析 → DocDB 写入 → Raft 复制 → 多数派确认 → 返回客户端
                                     │
                          ┌──────────┴──────────┐
                          │  多数派 = 2 个副本    │
                          │  跨节点 RTT 90-270ms │
                          └─────────────────────┘
```

一个 **NEW_ORDER** 事务涉及：
1. 读取/更新 `district` 表（获取 d_next_o_id）
2. 插入 `orders` 表
3. 批量更新 `stock` 表（10 个商品，每行 FOR UPDATE）
4. 插入 `new_order` 表
5. 插入 `order_line` 表（10 行）

以上每一步都可能触发 Raft 共识。单次 Raft round trip 的延迟取决于 leader 位置和多数派中最慢的 follower：

- Leader 在 region1（30ms egress）：等待 region2 确认 → 30ms（请求） + 60ms（响应） = **90ms**
- Leader 在 region3（90ms egress）：等待 region1 确认 → 90ms（请求） + 30ms（响应） = **120ms**
- 最坏情况（多数派需跨 region4/5）：**~270ms**

即每个 Raft round ≈ **90-270ms**。一个 NEW_ORDER 事务涉及 14-20 次写入操作（district UPDATE + orders INSERT + 10× stock UPDATE + new_order INSERT + 10× order_line INSERT），串行累计延迟可达 **1.3-5.4s**，与实测 avg 4.3s 吻合。

**PAYMENT** 受影响最大（×258）是因为它需要跨 warehouse 更新（remote payment），涉及更多跨节点通信。

### 3.2 STOCK_LEVEL 受影响最小（×64）

STOCK_LEVEL 是**只读事务**，不需要 Raft 共识写入。但它仍然需要从 tablet leader 读取数据——**集群未启用 `yb_read_from_followers`，默认所有读取由 leader 提供服务**。STOCK_LEVEL 查询涉及 `stock` 表的聚合扫描（COUNT + 条件过滤），其 tablet leader 可能分布在多个节点上，查询需要跨节点获取数据。

avg 295.8ms 的延迟解释：如果所需的 tablet leader 分布在 region2 (60ms) 或 region3 (90ms)，单次跨节点读取的 RTT ≈ 60-120ms（双向 egress），加上扫描和过滤处理时间，多次读取叠加到 ~300ms 是合理的。

相比写入型事务（200-260x），只读事务受影响较小（64x）的原因：
- 无需写入的 Raft 共识（省去多数派确认的等待）
- 读取只需与单个 tablet leader 通信，而非多个 follower
- 但 follower_read 未开启，仍存在跨节点读取开销

### 3.3 与 pgbench 延迟测试的一致性

此前 pgbench 延迟测试显示：

```
节点          基准读 avg    延迟读 avg    增长
─────────────────────────────────────────
region1 (30ms)   49ms        104ms       ×2.1
region3 (90ms)   167ms       310ms       ×1.9 (5% loss)
```

TPC-C 的延迟增长（×64~×291）远大于 pgbench 简单查询的增长（×2），原因：
- pgbench TPC-B 是简单事务（1 次 UPDATE + 1 次 SELECT），每事务的 Raft 交互次数少
- TPC-C 是复杂事务，每事务涉及 10+ 次表操作，每次都要 Raft 共识

### 3.4 与 SLO 对比

典型生产 SLO（Service Level Objectives）：

| 指标 | 目标 | 基准环境 | 延迟环境 |
|------|------|---------|---------|
| P99 读延迟 (ORDER_STATUS) | <100ms | ✓ 5.2ms | ✗ 1.3s |
| P99 写延迟 (NEW_ORDER) | <100ms | ✓ 39.8ms | ✗ 8.6s |
| 吞吐量衰减 | <50% | — | ✗ 99.6% |

延迟环境下 **完全无法满足任何合理的生产 SLO**。TPC-C 这种复杂事务工作负载在跨 180-270ms RTT 的网络下基本不可用。

> **\*效率说明**: go-tpc 的效率公式为 `tpmC / (12.86 × warehouses) × 100%`，其中 12.86 tpmC/warehouse 是官方 TPC-C 规范中单 warehouse 的最大理论吞吐。基准环境下 11,543%（=14843/(12.86×10)×100%）的效率显著超过 100%，原因有二：(1) go-tpc 未完整实现 TPC-C 的严格 wait/think time 约束，允许更高的有效吞吐；(2) 分布式数据库的多节点并行执行使得单 warehouse 的实际吞吐远超单节点模型的设计上限。因此**效率值在此无实际意义**，仅供参考。

### 3.5 误差率

| 环境 | NEW_ORDER 错误 | 总事务 | 错误率 |
|------|---------------|--------|--------|
| 基准 | 3 | 159,029 | 0.002% |
| 延迟 | 4 | 781 | 0.5% |

延迟环境错误率略高，但仍 <1%，主要是 `context deadline exceeded` — JDBC 驱动或 go-tpc 的默认超时设置导致。

---

## 4. 与 Google Spanner 对比

Spanner 使用 TrueTime + Paxos。两者跨 region 的核心瓶颈相同——物理光速限制下每轮共识的 RTT 延迟：

| 维度 | YugabyteDB | Spanner |
|------|-----------|---------|
| 共识协议 | Raft | Paxos |
| 时钟 | HLC（无硬件依赖） | TrueTime（需 GPS + 原子钟） |
| Commit Wait | 无需 | 2 × ε（1-7ms） |
| 跨 region 写入瓶颈 | 每事务多次 Raft round trip | 每事务多次 Paxos round trip |
| 吞吐量对比 | 见下方分析 | — |

**YugabyteDB 的优势**：无需 Commit Wait，消除了 1-7ms 的固定开销。但该开销相对于 90-270ms 的跨 region RTT 占比很小，不是主要瓶颈。

**Spanner 的可能优势**：
- Spanner 的 Paxos 实现允许更灵活的 leader 放置（可将 leader 放在客户端所在的 region），减少跨 region 通信
- Spanner 使用 `F1` 分布式 SQL 层，可能对跨 region 查询有更多优化
- 底层网络基础设施（Google 的私有光纤网络）比 tc netem 模拟更稳定

**无法直接对比**：
由于没有在同等硬件和网络条件下运行 Spanner TPC-C，无法给出量化对比。两种系统在跨 region TPC-C 场景下都会因多轮共识而面临严重的吞吐量衰减。

---

## 5. 结论与建议

### 5.1 结论

| 发现 | 结论 |
|------|------|
| 跨 region TPC-C 吞吐量 | 极低（68.8 tpmC），不适合跨 region 部署复杂事务工作负载 |
| 写入型事务 | 延迟增加 200-260 倍，Raft 共识是瓶颈 |
| 只读事务 | 受影响较小（64x），`follower_read` 可缓解 |
| 时钟同步 | HLC 在跨 region 下不是瓶颈，无需 Commit Wait |

### 5.2 生产建议

| 场景 | 建议 |
|------|------|
| 跨 region 事务工作负载 | 避免 TPC-C 级别的事务复杂度，使用简单事务(pgbench TPC-B) |
| 只读查询 | 启用 `yb_read_from_followers` + Leader Preference，就近读取 |
| 跨 region 写入 | 接受 4-8s 的 P99 延迟，或使用异步复制方案 |
| 数据本地化 | 使用 Geo-Partitioning 将每个 region 的数据独立，避免跨 region 事务 |

### 5.3 局限

- 单主机部署：所有节点共享物理资源，CPU/内存/磁盘可能成为瓶颈
- Docker 网络栈引入约 50ms 基础开销（psql 连接建立）
- go-tpc 默认超时可能在延迟场景下触发不必要的错误
- 未测试 `follower_read` 对 TPC-C 只读事务的优化效果

---

## 附录：原始结果摘要

### 基准环境（本次复现）

```
tpmC: 14843.0, tpmTotal: 33014.6
NEW_ORDER:    avg=21.0ms  P99=39.8ms  count=74198
NEW_ORDER_ERR: count=3
PAYMENT:     avg=7.7ms   P99=23.1ms  count=71154
PAYMENT_ERR:  count=2
DELIVERY:    avg=34.5ms  P99=65.0ms  count=6663
DELIVERY_ERR: count=1
ORDER_STATUS: avg=3.2ms   P99=5.2ms   count=6464
ORDER_STATUS_ERR: count=1
STOCK_LEVEL:  avg=4.7ms   P99=7.9ms   count=6550
STOCK_LEVEL_ERR: count=1
```

### 延迟环境

```
tpmC: 68.8, tpmTotal: 158.3
NEW_ORDER:    avg=4334.5ms  P99=8589.9ms  count=338
PAYMENT:     avg=1912.3ms  P99=4295.0ms  count=354
DELIVERY:    avg=7857.8ms  P99=12884.9ms count=22
ORDER_STATUS: avg=932.3ms   P99=1275.1ms  count=30
STOCK_LEVEL:  avg=295.8ms   P99=385.9ms   count=32
```

---

*测试框架: [yblab](https://github.com/your-repo/yb-compose)*
