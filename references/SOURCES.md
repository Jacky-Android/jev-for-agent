# Sources 与核查范围

核查日期：2026-10-04。遇到当前接口/schema/版本冲突，优先级固定为：当天 TypeSafe Docs/API > 官方 SDK 类型 > OpenRouter 官方 Decisions 文档 > TypeSafe 官方 Skill > 官方 Blog > Datawhale > Gallery > 用户 PDF > 第三方 MCP README。第三方 tool 名称与 envelope 都是 implementation-specific。

## 第一手接口与技能规范

- [TypeSafe API](https://docs.typesafe.ai/api)：/systemone、state/questions 与响应合约。
- [TypeSafe models](https://docs.typesafe.ai/models)：alias、当前 release、固定版本可不出现在模型目录的边界。
- [Choice](https://docs.typesafe.ai/primitives/choice)、[Score](https://docs.typesafe.ai/primitives/score)、[Noul](https://docs.typesafe.ai/primitives/noul)、[Advanced](https://docs.typesafe.ai/primitives/advanced)：原语与结构化描述。
- [Confidence](https://docs.typesafe.ai/confidence)、[文档索引](https://docs.typesafe.ai/llms.txt)：概率、置信度、上下文和 Python/JS SDK 章节。
- [System One 官方介绍](https://typesafe.ai/blog/introducing-system-one-models-and-jev)：System One/Two、RLCD、校准与类型空间的定位。
- [TypeSafe 官方 skill](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md)：开发指导；本项目实现额外的运行时 preflight/compiler/adapters。
- [OpenRouter Decisions](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)：alpha Decisions endpoint 与 body。
- [OpenRouter models](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties)：output_modalities=decisions 过滤。
- [OpenRouter Jev 指南](https://openrouter.ai/docs/guides/community/jev)、[教程](https://openrouter.ai/blog/tutorials/how-to-use-jev/)：模型路由、System One 兼容路径。
- [Agent Skills 规范](https://agentskills.io/specification)：SKILL.md、name/description 与渐进披露。
- [Claude Code Skills](https://code.claude.com/docs/en/skills)：个人/项目目录和 slash invocation。
- [Codex Skills](https://learn.chatgpt.com/docs/build-skills)：个人/项目目录、显式调用及发现机制。

## 架构与实践材料

[Datawhale Jev Cookbook](https://datawhalechina.github.io/jev-cookbook/)：已抓取其导航下 117 个页面，重点阅读开始、核心概念、state/questions/answers、三个 primitive、批量与依赖、置信度、架构模式、API/SDK/Agent Skill 及 cookbook。吸收的工程规则包括：同 state 独立判断、完整 rubric、程序门控、扇出成本、评分归一化、工具执行边界。

[Jev Gallery Guides](https://jevgallery.com/guides/)：抓取 18 个 guide 子页面，覆盖 API/提示、MCP、Claude Code、分类、RAG、浏览器、审核、引用核验、语义测试、写作检查、Agent 流程与回退。工具启动/发现/推理分层在 doctor 与报告中分别实现。

用户提供《JEV 中文知识库_详细学习版》PDF：真实抽取了 71 页、约 6.28 万字符，阅读其定义、Primitive、Confidence、模式、SDK/API/MCP、18 个 Cookbook、18 个 Guide 与版本边界。它用于概念及实践补充，不覆盖当天官方 API。出于包体与版权考虑，不将用户 PDF 或第三方全文复制进交付包。

下载 URL 清单见 [source-inventory.json](source-inventory.json)。downloaded 表示成功取得内容，不表示每篇都逐行审计，也不表示其中所有历史示例都适用于当前版本。实现所依赖的 endpoint、字段和模型另外由当天官方资料及真实 API 回包核实。

## 已解决的版本/实践差异

1. 普通 OpenRouter 模型列表会默认文本输出；使用 decisions 过滤，不能把 jev-router 当 Decisions Jev。
2. 第三方 MCP 的 latest 映射可能是固定 slug；实际模型优先记录真实上游响应。MCP 回包只给请求 slug时不补造 canonical 日期版本。
3. MCP 缓存包 0.13.0 与 initialize 0.12.0 不一致，分别记录。
4. 原生 Noul 无独立 confidence。第三方 certainty 必须注明 derived。
5. 直接 HTTP Score 保留 legend；专项 MCP review 返回固定维度、可能不带 legend，不能冒充完整任意 rubric 接口。
6. TypeSafe API 比本地规范更宽松之处已注明；本地 validator 不声称覆盖全部 API 功能或 token 限制。

## 可复查的实际证据

reports/doctor.json 是握手与工具发现快照；reports/model-discovery.json 是模型目录检查；reports/mcp-live-smoke.json 是宿主专项工具原始结果；reports/live-verification.json 是 HTTP 三原语真实响应；reports/end-to-end-jev.json 是真实任务判断。离线 fixtures 保存在 tests，不能用于这些 live 报告。
