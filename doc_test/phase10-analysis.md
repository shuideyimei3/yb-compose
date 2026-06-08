# 实验 10: TPC-C 吞吐量

> 核心对应 `doc/architecture.md`: 使用 TPC-C Benchmark 测量吞吐量，观察复杂事务在分布式数据库中的成本。

## 数据来源

| Run ID | 状态 | 耗时 | tpmC | tpmTotal | Efficiency |
|---|---:|---:|---:|---:|---:|
| `20260608T082336Z` | PASS | 355s | 14784.6 | 32706.6 | 11496.6% |
| `20260608T085229Z` | PASS | 355s | 15196.0 | 33774.6 | 11816.5% |
| `20260608T093857Z` | PASS | 356s | 14864.4 | 32963.8 | 11558.6% |
| 平均 | - | 355s | 14947.0 | 33148.3 | 11622.4% |

## 测试配置

| 参数 | 值 |
|---|---:|
| 工具 | go-tpc |
| Warehouses | 10 |
| Threads | 8 |
| Duration | 5m |
| 集群 | 5 节点 RF=3，无额外网络延迟 |

## 结果分析

三次 tpmC 分别为 14784.6、15196.0、14864.4，波动范围约 2.8%，说明基准环境下 TPC-C 结果可复现。

TPC-C 是复杂事务负载，NEW_ORDER、PAYMENT、DELIVERY 等事务涉及多表读写和多轮 SQL 操作。即使没有额外跨 region delay，RF=3 写入仍需要 Raft 多数派确认。因此该结果不是单机 OLTP 上限，而是 5 节点 YugabyteDB 在同主机 Docker 模拟环境中的分布式事务吞吐。

Efficiency 超过 100% 不是生产意义上的 TPC-C 合规效率。go-tpc 的实现和参数不等同于完整 TPC-C 审计口径，该字段只用于同一工具、同一配置下的相对比较。

## 与 architecture.md 的关系

`architecture.md` 要求用 TPC-C 衡量吞吐量。三次测试给出稳定基准：在无额外 WAN delay、10 warehouses、8 threads 下，YugabyteDB 可达到约 1.5 万 tpmC。若引入实验 3 的跨 region delay，复杂事务会因多轮 Raft 和多表写入被进一步放大；本组数据作为后续 WAN TPC-C 对比的基准。

## 结论

TPC-C 基准吞吐稳定，平均 tpmC 约 14947。该结果证明测试平台和 go-tpc 工具链可用，但不能单独说明真实全球部署性能；跨地域事务性能必须结合实验 3 的 RTT 和实验 4/7/9 的故障路径解释。
