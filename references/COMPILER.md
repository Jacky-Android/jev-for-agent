# 自然语言 → Decision Packet

编译器分成两层：Agent 负责理解自然语言、取证与语义分解；Python 负责静态验证并生成 HTTP/MCP packet。没有隐藏 LLM 调用，也不把正则匹配伪装为自然语言理解。

## Agent 编译约定

1. 从任务提取 goal、inputs、constraints、candidate_actions、risk、required_output。
2. 读取当前文件/日志/来源，填入最小 state，保留原文语言。
3. 将步骤标记为 semantic_judgment、deterministic_code、generative_work、tool_execution。
4. 只有 semantic_judgment 写 question。每题包含 type、完整 instructions、适当 criteria。其他步骤给 description。
5. 独立问题可同包；依赖上题答案取证的步骤下一轮再编译。`depends_on_answers` 非空会拒绝。
6. 没有合适语义判断时直接由 Agent/Code 完成任务，不发 Jev 请求。

完整可执行计划见 [triage_plan.json](../examples/triage_plan.json)。

```bash
python3 scripts/compile_packet.py examples/triage_plan.json --output packet.json
python3 scripts/validate_packet.py packet.json
python3 scripts/evaluate.py packet.json --provider openrouter --output result.json
```

compile 和 validate 不发送网络请求，不生成答案。evaluate 才付费调用。候选来自实际目标与证据，不能为了让 schema 通过而发明事实。静态依赖提示不能检测所有语义依赖，Agent 仍应审阅问题关系。

结果回来后读取原始概率、检查证据 freshness 与授权，再执行允许的操作。示例 `.85` 是可调 policy，不能推广成官方推荐。风险高或证据不足时走 review/gather_more_evidence。用户的新信息可以使旧 packet 失效。
