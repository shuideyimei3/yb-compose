# 实验 1: 环境搭建与架构分析

> 核心对应 `doc/architecture.md`: 整体架构、时钟同步机制、共识协议、数据分区与就近读。

## 数据来源

三次完整复现均通过：

| Run ID | 状态 | experiment-01 耗时 |
|---|---:|---:|
| `20260608T082336Z` | PASS | 3s |
| `20260608T085229Z` | PASS | 3s |
| `20260608T093857Z` | PASS | 4s |

## 实验目的

验证 YugabyteDB 作为全球分布式数据库原型时的基础结构是否满足后续测试前提：

- 5 节点 YSQL 集群可用
- RF=3 所需的 3 个 Master 和 5 个 TServer 正常
- HLC 时钟读数单调且集群内可观测
- region1-region5 表空间可创建，支撑 Geo-Partitioning 分析

## 三次复现结果

| 指标 | Run 1 | Run 2 | Run 3 | 结论 |
|---|---:|---:|---:|---|
| 可见节点数 | 5 | 5 | 5 | 稳定 |
| Master daemons | 3 | 3 | 3 | 满足 RF=3 元数据 quorum |
| TServer daemons | 5 | 5 | 5 | 满足 5 region 模拟 |
| `now()` 漂移 | 0.000ms | 0.000ms | 0.000ms | 同主机 Docker 共享系统时钟 |
| region 表空间 | 5 | 5 | 5 | Geo-Partitioning 前提成立 |

三次 Master Leader 均位于 region1 对应容器，但容器 ID 每次不同：

| Run ID | Master Leader |
|---|---|
| `20260608T082336Z` | `aa16b92c7f7c:7100` |
| `20260608T085229Z` | `cdc9bbb2c374:7100` |
| `20260608T093857Z` | `0fbb7ab48f1f:7100` |

## 架构分析

YugabyteDB 使用 HLC 而不是 Spanner 的 TrueTime。三次测试中 `now()` 漂移为 0ms，主要原因是所有容器运行在同一宿主机，并不代表真实跨地域物理时钟可以做到微秒级一致。该结果只能说明测试环境下没有额外物理时钟误差，后续时钟偏移实验需要主动注入偏差。

Raft 拓扑稳定为 3 Master + 5 TServer。Master 管理元数据和 tablet 分配，TServer 承载数据读写。RF=3 意味着写入需要多数派确认，这是后续延迟、故障切换、扩展性测试的核心性能开销来源。

region1-region5 表空间均创建成功，说明可以在 YSQL 层表达 region 维度的数据放置约束。后续实验并未完整展开业务级 geo-partitioned schema，而是重点验证网络延迟、Raft 共识和故障行为。

## 结论

基础架构三次复现稳定。该环境适合作为全球分布式数据库的单机模拟平台，但必须明确局限：它模拟的是多 region 拓扑和网络条件，不是真实多物理地域硬件环境。后续所有延迟和吞吐结论都应在这个前提下解释。
