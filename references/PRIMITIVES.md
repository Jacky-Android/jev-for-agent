# Primitive 使用参考

固定的“原理 → 理论根基 → 定义数据 → 定义问题 → 调用 → 解读结果”模板见 SKILL.md。这里补充输入结构、边界和常见陷阱。

| Primitive | criteria | 返回字段 | 适合 | 不适合 |
|---|---|---|---|---|
| choice | 1–255 个命名候选映射 | choice, probabilities, confidence（若返回） | 有限候选分类、路由 | 混合多个独立维度 |
| score | 2–10 项有序量规数组 | score, legend, probabilities, confidence（若返回） | 等级、程度、影响 | 精确价格、算术、计数 |
| noul | 可选 true/false 描述 | noul = P(true) | 单个明确条件 | 程度评分、伪造原生 confidence |

每题必须包含完整 instructions；同一请求的问题分别针对同一个 state 独立判断。API 支持结构化 instructions/criteria 描述；本 validator 同时支持非空文本、对象与数组。Choice API 允许某些空描述的用法，本 skill 为避免歧义主动拒绝。Score legend 的 HTTP JSON 索引为字符串；SDK 可能用整数索引，适配层不能默默丢弃映射。

## 例子与调用

- [choice.json](../examples/choice.json)：将发布说明归入具体主题。
- [score.json](../examples/score.json)：沿完整等级描述判断迁移行动程度。
- [noul.json](../examples/noul.json)：发布说明是否明确要求运行迁移。
- [mixed_questions.json](../examples/mixed_questions.json)：共享 state 的独立问题。
- [document_classification.json](../examples/document_classification.json)：中文文档分类输入，未声称中文准确率已验证。

```bash
python3 scripts/validate_packet.py examples/choice.json
python3 scripts/verify_primitives.py --provider openrouter --primitive choice
python3 scripts/verify_primitives.py --provider openrouter --primitive score
python3 scripts/verify_primitives.py --provider openrouter --primitive noul
```

相同 Score 均值可能来自集中或双峰分布，要看 legend 和分布才能解释。Noul .02 表示强烈支持 false，.5 表示不确定。wrapper 若给出 abs(2p−1)，只能记为 derived certainty。所有示例输入与真实验收响应分目录保存，示例概率不是测试替身。
