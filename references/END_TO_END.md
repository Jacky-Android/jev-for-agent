# 真实 Agent + Jev 案例

## 原任务与输入

“检查项目当前的测试失败，判断哪个问题应该最优先处理，然后修复。”本案例使用本包的**合成结算工程**，不是对用户真实项目的断言。契约明确 discount 是订单总额折扣比例，且该测试是核心结算必需校验。证据范围见 examples/checkout_project/CONTRACT.md；请勿把这个示例的“核心测试”标签复制到没有该事实的任务。

工具实际运行测试：fractional_discount 输入 [10,20], .1，期望27，得到29.9；no_discount 通过。初次 exit=1。完整观察保存在 reports/end-to-end-tests.json。

## 自然语言分工与请求

Agent 将任务分为：语义判断（错误类别/已证实影响/是否明确失败）、确定性计算（折扣公式）、生成（最小补丁）、工具动作（执行测试）。examples/triage_plan.json 经 compile_packet.py 生成 examples/triage_packet.json，三题直接读取同一份证据，不依赖彼此答案。

这是用户要求的三原语集成教学演示。实际只有这一处明确算术契约错误时，Agent 可直接修复，无需为安装了 Jev 而额外付费。

## 真实 Jev 结果

通过 OpenRouter Decisions API，实际模型 typesafe/jev-1.13-20260917：

- Choice cause：logic_bug；对应概率 .99，confidence .98。
- Score impact：2；critical_block 等级概率1，confidence1；完整 legend 与分布保留。
- Noul blocks_core：.97；无独立 confidence。

usage input_tokens=612、output_tokens=86、cost=.000025704；latency_ms=928.31。见 reports/end-to-end-jev.json，含真实原始响应和 request_id。它不是 mock 回放。

## 门控与 Agent 修复

此次是用户授权的可逆合成工程修复，证据刚从工具取得且完整；示例 gate .85 将三题路由 act，意思是允许使用判断，不提供操作系统权限。Agent 再检查源代码：原实现减去一个绝对数，违反比例契约，改为 `sum(values) * (1 - discount)`。这是 Agent 的补丁，Jev 没有修改文件。

reports/end-to-end.patch 保存实际差异。随后实际运行两项测试，两项通过，exit=0；不是根据 Jev 判断推测测试会成功。复跑记录与 gate 结果见 reports/end-to-end-tests.json。

## 复现

复制 examples/checkout_project 的 order.py、test_order.py 到临时目录，运行 `python3 -m unittest -v`。将 order_before.py 的内容替换临时 order.py 可观察原失败。重新运行 evaluate.py 会产生新的真实付费请求和新概率，不能指望与报告逐位一致。

## 非编程案例

已真实验证的 examples/choice.json 将发布说明分成 migration / password / none；Jev 选择 migration。它使用文本语义分类，不依赖源码。中文服务通知分类的完整独立输入另见 examples/document_classification.json，可用 validate_packet.py 静态校验、evaluate.py 实际调用；未调用时不得说中文验证通过。
