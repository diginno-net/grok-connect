---
name: connect
description: 为 Grok Build 挂载或卸载第三方模型供应商（GLM/智谱、DeepSeek、opencode Zen、阿里云、ChatGPT OAuth 等）。当用户输入 /connect、要求"添加供应商""接入 API key""切到 GLM/DeepSeek""用 Grok 以外的模型"，或想查看有哪些供应商时使用。
argument-hint: "[供应商?] [模型?]  ·  留空 = 列出"
allowed-tools: shell
disable-model-invocation: false
---

# 目标

Grok 没有供应商选择界面——`grok login` 只负责 xAI 登录，第三方供应商必须手写进 `config.toml`。
本 skill 通过 `grok-connect` CLI 取代这道手工活。

密钥**绝不**写入 `config.toml`。所有供应商都指向 `grok-cred` 助手，由它去读 opencode 的密钥库、
Codex 的密钥库，或环境变量。

# 工作方式

1. **先跑 `grok-connect list`**，把表格给用户看。`status` 一列直说哪些能挂：`ready`（就绪）·
   `attached`（已挂载）· `unsupported …`（不支持）。
2. 用户没指定供应商就问一次，并依据表格给建议。不要替用户做决定。
3. 查看有哪些模型：`grok-connect models <供应商>`。
4. 挂载：`grok-connect add <供应商> [模型…]`。不传模型则取 registry 前三个；用户点名了模型
   就原样传过去。
5. 卸载：`grok-connect remove <供应商>`。
6. `add` 会**对每个模型真实调用一次接口**并打印 HTTP 状态码——把结果念给用户听。之后随时可用
   `grok-connect test <供应商>` 复查。
   **`grok models` 能列出模型不代表它能用**——`base_url` 写错照样出现在列表里，直到聊天时才
   报 404。只认 `test` 那一列。
7. 能用的模型，告诉用户输入 `/model <名字>` 或 `grok -m <名字>`。新模型下一个会话才出现。

# 必须守住的边界

- **绝不主动挂 ChatGPT。** `grok-connect add chatgpt` 是拿 ChatGPT Plus/Pro 订阅走
  `chatgpt.com/backend-api/codex`——**那不是公开 API，违反 OpenAI 条款，有封号风险。**
  只有用户直接要求时才执行，且必须先讲清这个风险。
- 供应商标记为 `unsupported` 时，照表格给出原因，不要绕路硬上。
- 配额用尽 / 余额不足是账户问题，不是配置问题——就这么如实报告。
- 在 TUI 里切换模型时 Grok 会**重写 `config.toml` 并删掉所有注释**。用户动过模型选择器之后，
  回头检查 `[models] default`。
