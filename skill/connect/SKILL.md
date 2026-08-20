---
name: connect
description: Attach or detach third-party model providers for Grok Build (GLM/Z.ai, DeepSeek, opencode Zen, Alibaba, ChatGPT OAuth…). Use when the user types /connect, asks to "add a provider", "plug in an API key", "switch to GLM/DeepSeek", "use a model other than Grok", or wants to see which providers are available.
argument-hint: "[provider?] [model?]  ·  empty = list"
allowed-tools: shell
disable-model-invocation: false
---

# Goal

Grok has no provider picker — `grok login` only authenticates with xAI, and third-party
providers must be hand-written into `config.toml`. This skill replaces that, via the
`grok-connect` CLI.

Keys are **never** copied into `config.toml`. Every provider points at the `grok-cred`
helper, which reads opencode's key store, Codex's, or environment variables.

# How to work

1. **Always run `grok-connect list` first** and show that table to the user. The `status`
   column states plainly what can be attached: `ready` · `attached` · `unsupported …`.
2. If the user hasn't named a provider, ask once, with suggestions from the table. Don't pick
   for them.
3. To see what models exist: `grok-connect models <provider>`.
4. Attach: `grok-connect add <provider> [model…]`. With no models given it takes the first
   three from the registry. If the user named specific models, pass exactly those.
5. Detach: `grok-connect remove <provider>`.
6. `add` **calls the real endpoint** for each model and prints the HTTP status — read that
   result back to the user. Re-check any time with `grok-connect test <provider>`.
   **`grok models` listing a model does NOT prove it works** — a wrong `base_url` still shows
   up in the list and only fails at chat time with a 404. Trust only the `test` column.
7. For models that work, tell the user to type `/model <name>` or `grok -m <name>`. New models
   only appear in the next session.

# Boundaries to hold

- **Never attach ChatGPT on your own initiative.** `grok-connect add chatgpt` uses a ChatGPT
  Plus/Pro subscription through `chatgpt.com/backend-api/codex` — **not a public API, against
  OpenAI's terms, and it can get the account suspended.** Only run it when the user asks
  directly, and state that risk first.
- If a provider says `unsupported`, give the reason from the table; don't try to work around it.
- Out of quota / out of balance is an account problem, not a config problem — report it as such.
- Grok **rewrites `config.toml`** when the model is switched in the TUI, and **strips all
  comments**. After the user plays with the model picker, re-check `[models] default`.
