# 实验 6: 非均匀延迟与 Leader 放置

> 核心对应 `doc/architecture.md`: 共识协议、Leader 放置、就近读写策略。

## 数据来源

| Run ID | 状态 | 耗时 | Master Leader |
|---|---:|---:|---|
| `20260608T082336Z` | PASS | 60s | `772edc608f12:7100` |
| `20260608T085229Z` | PASS | 56s | `78c195c7a2cf:7100` |
| `20260608T093857Z` | PASS | 57s | `782bbb465741:7100` |

## 实验目的

注入非均匀延迟，观察 Raft Master Leader 是否会自动迁移到最低延迟节点，并检查 tablet leader 放置对读写路径的影响。

## 延迟配置

| 节点 | Delay |
|---|---:|
| yb-1 | 10ms |
| yb-2 | 25ms |
| yb-3 | 50ms |
| yb-4 | 75ms |
| yb-5 | 100ms |

## 结果

三次测试均得到同一类结论：Master Leader 由历史选举和运行状态决定，不会因为当前网络延迟最低而自动迁移。脚本输出均提示优化放置需要 Leader Preference 或显式重平衡。

Tablet Leader 分布可查询，但默认配置下不保证与客户端最近，也不保证集中在低延迟 region。换言之，单纯设置网络延迟并不会触发 YugabyteDB 自动重排 leader 到最优位置。

## 分析

Raft leader 选举目标是保证一致性与可用性，不是持续求解全局最低延迟。已有 leader 只要仍能维持 quorum，一般不会因为其他节点更低延迟而让位。对全球分布式数据库而言，这意味着业务要主动配置数据和 leader 的地理偏好。

## 结论

非均匀延迟环境下，YugabyteDB 不会自动选择最低延迟节点作为 leader。若要优化就近读写，需要结合 Geo-Partitioning、leader preference、tablet leader 重平衡和客户端接入点设计。
