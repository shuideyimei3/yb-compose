# 实验 1: 环境搭建与架构分析

> **测试日期**: 2026-06-07
> **环境**: 5 节点 YugabyteDB RF=3（Docker Compose 单主机部署）
> **配置**: NET_DELAY_MS=1（基准环境，无额外延迟）

---

## 1. 实验设计

### 1.1 目的

验证 5 节点 RF=3 集群的基础架构：
- HLC（Hybrid Logical Clock）时钟同步
- Raft 共识拓扑
- Geo-Partitioning 表空间配置

### 1.2 集群拓扑

| 节点 | Host ID | Region | 角色 |
|------|---------|--------|------|
| yb-1 | 05c582e3f247 | region1 | Master Leader + TServer |
| yb-2 | 9f6f0d9baec5 | region2 | Master Follower + TServer |
| yb-3 | 8b1a35ff63a4 | region3 | Master Follower + TServer |
| yb-4 | bc736ac87a7d | region4 | TServer only |
| yb-5 | 28e22e067069 | region5 | TServer only |

---

## 2. 结果

### 2.1 HLC 时钟同步

```
     host     |         current_time          
--------------+-------------------------------
 05c582e3f247 | 2026-06-07 13:08:44.968966+00
 28e22e067069 | 2026-06-07 13:08:44.968966+00
 8b1a35ff63a4 | 2026-06-07 13:08:44.968966+00
 9f6f0d9baec5 | 2026-06-07 13:08:44.968966+00
 bc736ac87a7d | 2026-06-07 13:08:44.968966+00
```

**所有 5 个节点的 `now()` 完全一致**（精确到微秒），验证了 HLC 在同主机部署下的时钟同步能力。

### 2.2 Raft 共识拓扑

```
     host     | node_type | cloud | region  
--------------+-----------+-------+---------
 05c582e3f247 | primary   | cloud | region1
 9f6f0d9baec5 | primary   | cloud | region2
 8b1a35ff63a4 | primary   | cloud | region3
 bc736ac87a7d | primary   | cloud | region4
 28e22e067069 | primary   | cloud | region5
```

- 5 个节点均为 `primary` 类型
- Master Leader 位于 region1（通过 API 确认）
- 3 个 Master（1 Leader + 2 Follower）分布在 region1/2/3
- 2 个纯 TServer 在 region4/5

### 2.3 Geo-Partitioning 表空间

```
 spcname 
---------
 region1
 region2
 region3
 region4
 region5
```

5 个 region 表空间全部创建成功，每个表空间配置了 `replica_placement` 约束，将副本固定到对应 region。

---

## 3. 分析

### 3.1 HLC 时钟同步机制

YugabyteDB 使用 HLC（Hybrid Logical Clock）而非 Spanner 的 TrueTime：

| 维度 | HLC | TrueTime |
|------|-----|----------|
| 硬件依赖 | 无 | GPS + 原子钟 |
| 时钟精度 | 逻辑单调递增 | ±ε 不确定性窗口 |
| Commit Wait | 无需 | 2×ε (1-7ms) |
| 跨 region | 依赖 NTP 同步 | 依赖专用硬件 |

在同主机部署下，所有节点共享同一物理时钟，HLC 的 `physical` 组件完全一致，`logical` 组件通过 Raft 通信自动递增，因此 `now()` 输出完全相同。

**注意**: 在真实跨 region 部署中，各节点物理时钟存在 NTP 同步误差（通常 <500ms），HLC 通过逻辑时钟保证单调递增，但 `now()` 不会完全一致。

### 3.2 Raft 拓扑结构

```
Master Quorum (3 节点):
  region1 (Leader) ←→ region2 (Follower) ←→ region3 (Follower)

TServer 集群 (5 节点):
  region1, region2, region3, region4, region5
  RF=3: 每个 tablet 有 3 个副本，分布在 3 个不同 region
```

- Master 负责元数据管理和协调 tablet 分配
- TServer 负责实际数据存储和 SQL 查询处理
- RF=3 意味着每个 tablet 的 3 个副本中，任意 2 个存活即可提供服务

### 3.3 Geo-Partitioning 的意义

创建 region-specific 表空间后，可以将表或分区绑定到特定 region，实现：
- **数据本地化**: 某些数据只存储在特定 region 的节点上
- **合规要求**: 数据不出特定地理区域
- **延迟优化**: 本地读取避免跨 region 通信

---

## 4. 结论

| 验证项 | 结果 |
|--------|------|
| 5 节点集群启动 | ✅ 全部 healthy |
| HLC 时钟同步 | ✅ 所有节点 now() 完全一致 |
| Raft 拓扑 | ✅ 3 Masters (1L+2F) + 5 TServers |
| Geo-Partitioning | ✅ 5 个 region 表空间创建成功 |

集群基础架构验证通过，可进行后续实验。
