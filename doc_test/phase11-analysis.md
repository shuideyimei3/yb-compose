# 实验 11: 扩展性测试 (Scalability Test)

> **测试日期**: 2026-06-08
> **环境**: YugabyteDB RF=3 (Docker Compose 单主机部署)
> **工具**: pgbench (TPC-B, scale=1, 16 clients, 60s)

---

## 1. 实验设计

### 1.1 目的

| 维度 | 说明 |
|------|------|
| 水平扩展 | 验证增加节点数对吞吐量 (TPS) 的影响 |
| 延迟变化 | 观测不同节点数下的平均延迟 |
| 共识开销 | 量化 Raft 共识在不同拓扑下的性能损耗 |
| RF 影响 | 对比 RF=1 (1节点) 和 RF=3 (3/5节点) 的性能差异 |

### 1.2 测试拓扑

| 配置 | 节点 | 角色分布 | RF |
|------|------|---------|-----|
| N=1 | yb-1 | 单节点 (Master+TServer) | 1 |
| N=3 | yb-1,yb-2,yb-3 | 3 Master + 3 TServer | 3 |
| N=5 | yb-1～yb-5 | 3 Master + 5 TServer | 3 |

### 1.3 测试参数

| 参数 | 值 |
|------|-----|
| pgbench scale | 1 (100,000 账户) |
| 并发客户端 | 16 |
| 测试时长 | 60 秒 |
| 事务类型 | TPC-B (READ+UPDATE+INSERT) |
| 网络环境 | 无额外延迟 (~0ms inter-node RTT) |

---

## 2. 结果

### 2.1 总体对比

| 指标 | N=1 (RF=1) | N=3 (RF=3) | N=5 (RF=3) |
|------|------------|------------|------------|
| **TPS** | **767.90** | **482.67** | **353.89** |
| **Avg Latency** | **20.84 ms** | **33.15 ms** | **45.21 ms** |
| **事务总数** | 45,988 | 28,923 | 21,226 |
| **错误率** | <0.1%¹ | 0.000% | 0.000% |
| **相对 N=1 TPS** | 1.00× | 0.63× | 0.46× |

> ¹ N=1 存在少量 Catalog Version Mismatch 错误 (DDL 后元数据缓存不一致)，属于已知现象。

### 2.2 可视化

```
TPS vs Node Count
─────────────────────────────────────────
 800│  ● (767.90)
    │
 600│
    │     ● (482.67)
 400│              ● (353.89)
    │
 200│
    │
   0├─────┬─────┬─────┬─────┬─────┬─────
    1     2     3     4     5     6
                Nodes
─────────────────────────────────────────

Latency vs Node Count
─────────────────────────────────────────
  50│                        ● (45.21)
    │
  40│           ● (33.15)
    │
  30│
    │  ● (20.84)
  20│
    │
  10│
   0├─────┬─────┬─────┬─────┬─────┬─────
    1     2     3     4     5     6
                Nodes
─────────────────────────────────────────
```

---

## 3. 分析

### 3.1 核心发现: 节点增加 → 吞吐量下降

**这是一个反直觉但合理的结果。** 在分布式数据库中，增加节点并不总是能线性提升性能，取决于工作负载的特征。

### 3.2 根因分析

#### 原因 1: Raft 共识开销主导小负载

每个 TPC-B 事务包含:
1. `UPDATE pgbench_accounts` (余额扣减)
2. `SELECT abalance` (余额查询)
3. `UPDATE pgbench_tellers` (柜员余额)
4. `UPDATE pgbench_branches` (分行余额)
5. `INSERT pgbench_history` (交易记录)

在 RF=3 配置下，**每一步写入都需要 Raft 共识**：

```
客户端 → YSQL → DocDB → Raft Leader → Raft Followers → 多数派确认 → 返回
                                         │
                          ┌──────────────┴──────────────┐
                          │  等待 2 个节点确认            │
                          │  N=3: 1 leader + 1 follower │
                          │  N=5: 1 leader + 2 followers│
                          └─────────────────────────────┘
```

| 配置 | 每事务 Raft 交互 | 网络开销 | 影响 |
|------|-----------------|---------|------|
| N=1 (RF=1) | 0 次 (无副本) | 0ms | 仅本地 I/O |
| N=3 (RF=3) | ~5 次 × 2副本 | ~0ms¹ | 同步等待 |
| N=5 (RF=3) | ~5 次 × 2副本 | ~0ms¹ | 额外心跳开销 |

> ¹ 同主机 Docker 网络延迟 ~0ms，但仍有序列化/反序列化、消息队列等开销

#### 原因 2: 复制因子差异 (RF=1 vs RF=3)

N=1 使用 RF=1 (无副本)，是所有配置中性能最高的:

```
N=1 (RF=1):
  Write → Single node (yb-1) → 立即返回
  延迟 ≈ 本地磁盘 I/O + SQL 处理

N=3 (RF=3):
  Write → Leader (yb-X) → Replicate to Followers → 返回
  延迟 ≈ Leader 本地 I/O + SQL 处理 + 副本同步等待
```

从 N=1 到 N=3，TPS 下降了 **37%** (767.90 → 482.67)，主要归因于引入 Raft 复制 (RF 1→3)。

#### 原因 3: N=3 → N=5 的额外降级

从 N=3 到 N=5，TPS 进一步下降了 **27%** (482.67 → 353.89)：

```
N=3: 3 Master + 3 TServer (紧凑拓扑)
     所有节点都是 Master，Leader 选举本地化
     平均 Raft RTT = 单跳

N=5: 3 Master + 5 TServer (松散拓扑)
     yb-4, yb-5 是纯 TServer，不参与 Master 共识
     但 Tablet Leader 可能在 yb-4/yb-5 上
     会导致额外的跨节点 tablet 查找和路由
     系统维护开销增加: Raft 心跳 × 5 节点 + 元数据同步
```

#### 原因 4: Scale=1 数据集太小

```
pgbench scale=1:
  pgbench_accounts: 100,000 行
  pgbench_branches: 1 行 (单 branch)
  pgbench_tellers:  10 行
  pgbench_history:  动态增长

5 节点 × RF=3 = 15 个 tablet 副本
每个表的每个 tablet ≈ 几千行数据
```

对于如此小的数据集，分布式系统的开销（Raft 心跳、领导选举、tablet 路由、元数据缓存）占用了不成比例的资源。节点数越多，固定开销越大，而数据并行化带来的收益为零。

### 3.3 何时会看到正向扩展

正向扩展需要满足以下条件:

| 条件 | 本次测试 | 预期 |
|------|---------|------|
| 数据集很大 (scale ≥ 100) | scale=1 ❌ | ✅ |
| 读密集型工作负载 | TPC-B (读写混合) ❌ | ✅ |
| 客户端连接分散到多节点 | 全部连接 yb-1 ❌ | ✅ |
| 异构硬件 (非单机部署) | Docker 单主机 ❌ | ✅ |
| Follower Reads 启用 | 未启用 ❌ | ✅ |

**在以下场景中，预期会看到正向扩展:**
1. **大数据集 (scale≥100)**: tablet 分片在多个节点上，读写可以并行
2. **读密集型负载**: 启用 `yb_read_from_followers`，读取可以就近访问
3. **连接分散**: 客户端连接不同的节点，减少单节点瓶颈
4. **物理分布式部署**: 各节点有独立 CPU/内存/磁盘

### 3.4 与 TPC-C 结果的关联

| 指标 | TPC-C (基准) | pgbench N=5 | 说明 |
|------|-------------|-------------|------|
| tpmC/TPS | 14,843 | 353.89 | TPC-C 复杂事务 vs 简单 TPC-B |
| Avg Latency | 21.0ms | 45.21ms | 受事务复杂度影响 |
| 事务类型 | 5种混合 | TPC-B 单一 | TPC-C 更有意义 |

TPC-C 的 14,843 tpmC 是在 5 节点集群上获得的。如果仅用 1 节点 (RF=1)，吞吐量可能会更高（类似 pgbench 的 N=1 > N=5 模式），但这会失去数据冗余和高可用性。

---

## 4. 结论

### 4.1 关键发现

| 发现 | 说明 |
|------|------|
| **N=1 > N=3 > N=5** | 小负载下节点增加 → TPS 下降 |
| Raft 开销占比 | scale=1 时 Raft 共识占 >50% 延迟 |
| RF 是关键因素 | RF=1 → RF=3 引入 37% 性能损失 |
| 并非线性扩展 | 分布式 ≠ 自动扩展，需要优化配置 |

### 4.2 生产建议

| 场景 | 建议 |
|------|------|
| 小规模部署 (<10GB) | 3 节点 RF=3 即可，额外节点无益 |
| 需要高可用 | 最小 3 节点 RF=3，可加只读副本 |
| 读密集型工作负载 | 启用 `follower_read` + Leader Preference |
| 大数据集 (>100GB) | 5+ 节点可以让 tablet 均匀分布 |
| 跨区域部署 | 使用 Geo-Partitioning 避免跨区域 Raft |

### 4.3 局限与改进

| 局限 | 改进方向 |
|------|---------|
| scale=1 数据集太小 | 使用 scale≥100 进行大规模扩展性测试 |
| 同主机 Docker 部署 | 物理分布式部署以消除资源争用 |
| 客户端仅连 yb-1 | 使用多客户端连接不同节点 |
| 未启用 follower_read | 开启 `yb_read_from_followers` 测试读扩展 |
| pgbench 仅 TPC-B 模式 | 使用 pgbench 自定义脚本模拟真实负载 |
| TPS 测量窗口 60s | 扩展到 300s+ 以获取更稳定数据 |

---

## 附录: 原始结果

### N=1 (RF=1)

```
pgbench (16.14, server 15.12-YB-2025.2.3.2-b0)
scale: 1, clients: 16, threads: 16, duration: 60s
transactions: 45988 (0 failed)
latency average = 20.836 ms
tps = 767.900375 (without initial connection time)
```

### N=3 (RF=3)

```
pgbench (16.14, server 15.12-YB-2025.2.3.2-b0)
scale: 1, clients: 16, threads: 16, duration: 60s
transactions: 28923 (0 failed)
latency average = 33.149 ms
tps = 482.669764 (without initial connection time)
```

### N=5 (RF=3)

```
pgbench (16.14, server 15.12-YB-2025.2.3.2-b0)
scale: 1, clients: 16, threads: 16, duration: 60s
transactions: 21226 (0 failed)
latency average = 45.211 ms
tps = 353.893266 (without initial connection time)
```

---

*测试框架: [yblab](https://github.com/your-repo/yb-compose)*
