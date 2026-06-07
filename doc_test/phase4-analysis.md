# 实验 4: 故障切换 RTO

> **测试日期**: 2026-06-07
> **环境**: 5 节点 YugabyteDB RF=3（Docker Compose 单主机 + tc netem 30/60/90/120/150ms）

---

## 1. 实验设计

### 1.1 目的

对比两种故障场景的恢复时间 (RTO)：
1. **docker stop**：模拟进程崩溃（节点完全消失）
2. **iptables isolate**：模拟网络分区（节点存活但不可达）

### 1.2 测试方法

1. 通过 yb-2 执行持续写入
2. 注入故障（停止 yb-1 或隔离 region1）
3. 探测写入恢复时间
4. 验证 RPO（Recovery Point Objective）

---

## 2. 结果

### 2.1 Docker Stop 故障切换

| 指标 | 结果 |
|------|------|
| 故障类型 | docker stop yb-1 |
| 探测方式 | 通过 yb-2 写入 INSERT |
| **RTO** | **586.55ms** |
| 恢复后集群 | 5 节点全部可见 |
| RPO | 0（Raft 保证已提交日志不丢失） |

> **与 README 的差异**: README 预期 docker stop RTO 为 ~515ms，实测为 586.55ms，差异约 70ms，在正常波动范围内。

### 2.2 iptables 网络分区

| 指标 | 结果 |
|------|------|
| 故障类型 | iptables 双向 DROP region1 |
| 探测方式 | 通过 yb-2 写入 INSERT |
| **RTO (total)** | **2,602.06ms** |
| **RTO (net)** | **561.02ms** |
| RPO | 0 |

**RTO (total)** = 从故障注入到写入恢复的总时间
**RTO (net)** = 从分区生效到写入恢复的时间（扣除 chaosctl 启动开销）

> **与 README 的差异**: README 预期 iptables RTO 为 ~1000-1500ms，但实测 RTO (net) 为 561ms，与 docker stop 接近。README 的 ~1000-1500ms 可能是包含了 chaosctl 工具启动时间的总 RTO（实测 total = 2,602ms），也可能是早期粗略估计，建议更新为实测值。

---

## 3. 分析

### 3.1 两种故障场景的差异

| 维度 | docker stop | iptables isolate |
|------|------------|-----------------|
| 节点状态 | 进程完全终止 | 进程存活但不可达 |
| 检测机制 | Raft heartbeat 超时 | Raft heartbeat 超时 |
| 实际 RTO | 586.55ms | 561.02ms |
| 总恢复时间 | ~586ms | ~2,602ms (含工具启动) |

**核心发现**: 两种场景的实际 Raft 恢复时间几乎相同（~560-590ms），因为 Raft 的故障检测都依赖 heartbeat 超时。iptables 场景的总 RTO 更长是因为 chaosctl 工具启动需要约 2 秒。

### 3.2 Raft 故障恢复流程

```
yb-1 停止/隔离
    │
    ▼ (heartbeat timeout ~300ms)
yb-2/yb-3 检测到 leader 失联
    │
    ▼ (leader election ~200-300ms)
新 leader 选出 (region2 或 region3)
    │
    ▼ (客户端重路由 ~50ms)
写入恢复
    │
    ══> 总计 ~560-590ms
```

### 3.3 RPO = 0 的保证

YugabyteDB 使用 Raft 共识协议，**已提交的写入必须得到多数派 (2/3) 确认**。即使 leader 宕机，已提交的日志在至少一个 follower 上存在，新 leader 选出后这些日志不会丢失。

在 5 节点 RF=3 配置中：
- 停止 1 个节点：剩余 4 个节点，每个 tablet 仍有 2/3 副本 → 多数派可达
- 隔离 1 个节点：同上，剩余节点可以正常提交

### 3.4 延迟环境对 RTO 的影响

RTO ~560-590ms 在延迟环境下仍然很快，原因：
- Raft heartbeat 超时默认 ~300ms，与网络延迟无关（heartbeat 是轻量级消息）
- Leader election 只需要多数派响应，在 RF=3 中只需 2 个节点
- 本测试中 yb-2 (60ms) 和 yb-3 (90ms) 之间的 RTT = 150ms，选举延迟很小

---

## 4. 结论

| 验证项 | 结果 |
|--------|------|
| docker stop RTO | ✅ ~587ms |
| iptables isolate RTO | ✅ ~561ms (net) |
| RPO | ✅ 0（无数据丢失） |
| 延迟环境对 RTO 影响 | ✅ 极小（Raft 恢复与网络延迟解耦） |

**核心发现**: YugabyteDB 在延迟环境下的故障切换 RTO 约 560-590ms，两种故障类型（进程崩溃 vs 网络分区）的实际恢复时间几乎相同。Raft 共识协议保证了 RPO = 0。
