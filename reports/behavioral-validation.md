# 独立 Agent 行为验证

基线（未提供本 skill）：给定结算失败观察，Agent 能分解问题，但产出 questions 数组、大写 primitive、非官方 options/selected 字段、错误 Score 范围和演示 Noul confidence；因此不能作为可调用 Jev packet。演示概率未被当作 live 证据。

带 skill 的独立新上下文验证：轻量 doctor 成功（PARTIAL），未启动 MCP、未付费推理。Agent 生成 plan/packet 并实际通过 compiler 与 validator（exit 0；static_only；warnings=[]），正确区分三原语、算术、修复和工具动作。解释 Noul .5 为不确定、confidence 不等于正确率，并明确无需 Jev 时可直接计算修复。未声称 live verified。

发现并处理：独立场景没有“核心结算测试”这一事实，因此评估 Agent 拒绝借用示例的该标签。交付案例现在附带明确合成工程契约和范围提醒；不得将示例事实迁移到用户项目。doctor 默认看不到宿主 tool schema，文档说明由 Agent 检查或通过 --agent-tools 导入。已改进编译器错误反馈：静态 ValidationError 显示不含输入值的规则消息；文件系统错误仍隐藏详情。

这是一组行为 smoke 验证，不是广泛模型评测，也不证明跨宿主一致性。真实 API 验收证据独立保存在 live-verification.json。
