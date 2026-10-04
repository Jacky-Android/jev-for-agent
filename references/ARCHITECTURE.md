# 组合模式

## Confidence-gated Routing

Jev 返回判断，代码做 schema、freshness、authorization 与阈值检查，Agent 执行。`jev_agent/policy.py` 提供 act/review/abstain/gather_more_evidence 的纯函数示例。action 权限由实际系统检查，传入 authorized=True 不构成权限系统。Noul 负结果的确定性高时可以接受该否定判断，但不得执行肯定分支。

## Intent Routing

Choice 对互斥意图分类；另起 Score 判断紧急度，避免混维度。候选中提供无法归类出口。实际动作绑定白名单代码，不能直接执行模型输出的 shell 字符串。

## Speculative Fan-out

对同一 state 的独立候选/问题批处理。只有预算允许时才提前执行可取消、无外部副作用的检索。多路写操作、发布和支付不能靠之后“选择一路”回滚。全局请求 deadline、成本和取消策略由宿主实现。

## Composite Scoring

将可解释的多个维度分别用 Score，保留各自 legend 与分布。最终权重、归一化和加总用代码，注明业务定义和缺失值处理。不同 rubric 的原始 index 不能直接比较；高平均分也不能抵消硬性失败条件。

## RAG / 引用核验 / 浏览器

RAG 可用 Score 评估 query-document 相关性，以代码排序；Noul 判断给定摘录是否支持具体断言。先由 Agent 取得真实来源，不把标题相似当作引用证据。浏览器由工具取得页面/候选，Jev 可在候选中判断目标，实际点击与确认仍归浏览器工具；页面变化必须重新取证。

## Agent generates → Jev judges → Agent revises

需要语义复核时最多两轮（示例默认），状态或证据未变化就不重复采样。成本或时间预算耗尽则报告未决。代码测试失败不能被 Jev 高 confidence 覆盖；单个高风险判断也不自动允许外部写入。
