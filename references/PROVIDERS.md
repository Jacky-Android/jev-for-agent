# Providers、MCP 与版本

核查日期：2026-10-04。接口会演进，升级前重查 [SOURCES.md](SOURCES.md)。

## 当前 HTTP 合约

| 项目 | TypeSafe Direct | OpenRouter |
|---|---|---|
| 认证 | TYPESAFE_API_KEY | OPENROUTER_API_KEY |
| 模型发现 | GET https://api.typesafe.ai/v1/models | GET https://openrouter.ai/api/v1/models?output_modalities=decisions&q=typesafe |
| 推理 | POST https://api.typesafe.ai/v1/systemone | POST https://openrouter.ai/api/alpha/decisions |
| 当前 alias | jev-latest | ~typesafe/jev-latest |
| 当前已确认 release | jev-1.13.0（官方模型文档） | typesafe/jev-1.13（目录）；真实响应 typesafe/jev-1.13-20260917 |

Body 为 `{model,state,questions}`。OpenRouter 普通模型列表默认筛选文本输出，可能只看到 Jev Router；该 chat router 不能代替 Decisions 模型。本项目不使用 Chat Completions。OpenRouter 新的兼容 `/api/v1/systemone` 路径不在本次实现/验收范围。

每个 Session 缓存一次模型目录。显式模型不在当前目录时拒绝静默替换。TypeSafe `/models` 可能只列 alias，固定 release 需用当天官方 models 文档补充确认；无凭据时不声称其实际推理通过。响应给出的 model 优先；若响应只有 alias 且请求已由当前资料确认固定版本，标记 `model_resolution=pinned_request`，否则 actual_model 为 null。

## 统一 Python 接口

```python
from jev_agent.runtime import Session
with Session(provider="openrouter") as session:
    result = session.evaluate(state, questions, model=None)
```

NormalizedJevResult 保留 provider、actual_model、reported_model、requested_model、model_resolution、request_status、answers、raw_response、usage、latency_ms、request_id、source_mode。`provider=openrouter` 是账单/接入路径，raw_response.provider 的 TypeSafe 是上游推理商。缺失 usage/request_id 保留 null；延迟是本地测得请求耗时，不是纯推理耗时。请求失败抛出可安全记录的异常，不造成功结果。

## Existing MCP

优先使用当前 Agent 已暴露且匹配任务的 tool，按实际 schema 调用。`ExistingMCP(call_tool, tool_metadata)` 支持通用 state/questions tool；`call_tool(name,args)` 由宿主提供。命令行 Session 可连接已配置的 stdio MCP，通过 initialize → tools/list → tools/call 使用同一适配层。URL/SSE/Streamable HTTP MCP 由宿主连接后提供 callback，本项目不自行实现远程 MCP 认证协议。

工具名不是标准。`capabilities()` 只标注候选能力；必须真实调用并校验才确认。专项 classify/noul/review 等可以由 Agent 直接调用，但固定 review rubric 不能冒充任意 Score。自动 CLI 遇到只有专项工具的 MCP 会明确阻止通用 packet；可使用已知相同账单 Provider 的 `--provider openrouter`，不自动换账单。

当前机器记录：Codex 配置了 `jev`；initialize 报 jev-mcp 0.12.0，本机缓存 npm 包 @jkudish/jev-mcp 0.13.0，JS SDK @typesafe-ai/sdk 0.6.0。版本差异照实保留，不取其中一个冒充模型版本。发现 12 个专项工具，无通用 state/questions tool。现有 MCP 的 classify/noul/review 已成功 smoke 调用，report 保存其原始包装响应；review 会省略 legend，因此完整三原语验收走同一 OpenRouter 账单的 HTTP。

## 环境与 SDK

Doctor 检查 Claude 用户/当前项目 MCP、Codex 用户/项目配置、可执行文件、当前 Python 环境包元数据、本地与 npm 缓存的 JS 包元数据。SDK 检测不代表曾通过 SDK 推理，也不穷举所有 virtualenv 或包管理器安装位置。Python SDK 标准方法为 TypeSafeClient.system_one，JS @typesafe-ai/sdk 为 systemOne；本项目直接使用 HTTP，避免为 runtime 强装 SDK。

识别 JEV_PROVIDER、JEV_MODEL、JEV_MCP_MODEL、TYPESAFE_DEFAULT_MODEL、TYPESAFE_BASE_URL、JEV_OPENROUTER_BASE_URL 及 MCP 相关环境变量；凭据只输出 configured/missing。空 .env.example 仅是说明，脚本不自动加载 .env。显式 CLI 优先于环境；已有 MCP 或明确 provider 失败时不自动改用另一账单。

## 错误与数据保护

默认可用 curl 时使用 HTTP/1.1；认证头和 payload 经 stdin 配置输入，不进入进程参数。可设置 JEV_HTTP_TRANSPORT=urllib 使用标准库。HTTPS、禁重定向、30 秒默认 deadline、最多两次尝试（上限三次）；仅 429/529 有界退避，超时/网络中断不重试以避免重复计费。curl 路径目前使用有界指数退避，未解析 Retry-After。

认证值、已知环境 secret、常见 token 模式不得进入 state/日志/异常；HTTP 错误正文隐藏。criteria/probabilities/legend 中的 password 等语义标签允许存在，但任何已知 secret 值仍被阻止。该检测不是通用 DLP：调用者仍需最小化私有数据。raw_response 涉及任务内容，报告应按数据敏感级别保存。不要开启 curl verbose 或打印配置。

自定义 HTTPS Base URL 是显式信任选择；先核实服务器兼容请求与响应 schema，再配置对应 Provider。不能仅凭 URL 或工具名宣称兼容。
