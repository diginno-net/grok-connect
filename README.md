# grok-connect

Attach third-party model providers to **Grok Build** (xAI's `grok` CLI) — GLM/Z.ai, DeepSeek,
opencode Zen, Alibaba, any OpenAI-compatible endpoint — without hand-editing TOML, and without
copying a single API key into a config file.

**English** · [Tiếng Việt](README.vi.md) · [中文](README.zh.md)

```
$ grok-connect list
provider             key     protocol          status      base_url
deepseek             api     chat_completions  attached    https://api.deepseek.com
opencode-go          api     chat_completions  attached    https://opencode.ai/zen/go/v1
zai-coding-plan      api     chat_completions  ready       https://api.z.ai/api/coding/paas/v4

$ grok-connect add zai-coding-plan glm-5.2 glm-4.7
attached 'zai-coding-plan' to /Users/me/.grok/config.toml
Calling the endpoint:
  ok   glm-5_2                  HTTP 200  works
  ok   glm-4_7                  HTTP 200  works

All working. Use: grok -m <model>  ·  or /model inside the TUI
```

---

## `/connect` inside the TUI

![The /connect slash command listing every provider, its auth type and whether it is attached](docs/connect-provider-table.png)

Type `/connect` and the agent runs `grok-connect list` for you, reads the table back, and asks
which provider to attach — it never picks for you. *(The skill ships in English, Vietnamese and
Chinese; the screenshot shows the Vietnamese build.)*

![The agent proposing a grok-connect add command with the full model list, and warning that only a successful HTTP status proves a model works](docs/connect-add-and-verify.png)

Note what it says at the bottom: **only a successful HTTP status counts as proof.** Appearing in
the registry or in `/model` does not mean the endpoint answers. New models show up from the next
grok session on.

---

## Why this exists

Grok Build is already a multi-provider client — its sampler speaks three protocols
(`chat_completions`, `responses`, Anthropic `messages`) and `[model.*]` blocks let you point at
any endpoint. What it does **not** have is a way to *use* that:

- `grok login` only authenticates with **xAI** (OAuth · device code · OIDC · an external auth binary).
- There is no `/connect`, no provider picker, no "paste your API key" screen.
- Adding a provider means writing three TOML blocks by hand and getting every field right.

`grok-connect` is that missing surface. It reads the [models.dev](https://models.dev) registry for
base URLs and model catalogues, resolves your key, writes the config, **and calls the endpoint to
prove the thing actually works**.

## What you get

| Piece | What it does |
|---|---|
| `grok-connect` | CLI: `list` · `models` · `add` · `test` · `remove`. Writes/removes the config blocks. |
| `grok-cred` | Credential helper wired into grok's `[auth_provider.*]`. Resolves keys at call time so **no secret is ever written into `config.toml`**. |
| `/connect` skill | The CLI, surfaced as a slash command inside the grok TUI. Ships in English, Vietnamese and Chinese. |
| `chatgpt-responses-shim` | *Optional, not installed by default.* Bridges grok to a ChatGPT subscription. **Read the warning below before touching it.** |

## Requirements

- [Grok Build](https://x.ai/cli) ≥ 1.0.5 (`grok --version`)
- Python 3.9+
- Keys from **one** of:
  - [opencode](https://opencode.ai)'s credential store (`~/.local/share/opencode/auth.json`) — used automatically, nothing to configure
  - environment variables — the names models.dev declares (`DEEPSEEK_API_KEY`, `ZHIPU_API_KEY`, `OPENCODE_API_KEY`, …) or `GROK_CRED_<PROVIDER>`

## Install

```sh
git clone <this-repo> && cd grok-connect
./install.sh                 # scripts into ~/.local/bin, /connect skill into every ~/.grok*
SKILL_LANG=vi ./install.sh   # Vietnamese skill (also: zh)
```

`install.sh` finds every grok home on the machine (`~/.grok`, `~/.grok-100`, …) and installs the
skill into each. Set `GROK_HOME` to target just one.

## Use

```sh
grok-connect list                              # who has a key, what's attached
grok-connect models zai-coding-plan            # model catalogue for a provider
grok-connect add zai-coding-plan glm-5.2       # attach (no model = first three)
grok-connect test zai-coding-plan              # re-verify any time
grok-connect remove zai-coding-plan            # detach
```

Or inside grok, type `/connect` and let the agent drive it.

New models appear in the **next** session — then `/model <name>` or `grok -m <name>`.

## What it writes

Three blocks per provider. Note there is no key anywhere:

```toml
[auth_provider.zai-coding-plan]
command = "grok-cred zai-coding-plan"

[model_providers.zai-coding-plan]
base_url = "https://api.z.ai/api/coding/paas/v4"
api_backend = "chat_completions"
auth_provider = "zai-coding-plan"

[model.glm-5_2]
model = "glm-5.2"
model_provider = "zai-coding-plan"
name = "glm-5.2 (zai-coding-plan)"
context_window = 1000000
```

Grok runs `grok-cred` before any turn that needs a token, caches the result in memory, and re-runs
it on expiry or rejection. Tokens never touch disk. A model backed by an auth provider is strictly
BYOK: **your xAI session token is never sent to a third-party endpoint.**

## Verifying — and why `grok models` is not proof

`grok models` only reads the config file. A model with a broken `base_url` still shows up in that
list; you find out at chat time, with a 404. `add` and `test` make a real HTTP call per model:

| HTTP | Meaning |
|---|---|
| 200 | works |
| 401 / 403 | key wrong or expired · key not entitled to this model |
| **402** | out of balance — **config is right**, top up and it runs |
| **404** | **wrong `base_url` or wrong model name** |
| **429** | out of quota / rate limited — **config is right**, wait for reset |

That split matters: 402 and 429 are account problems, 404 is your mistake.

## Gotchas worth knowing

- **Don't append `/v1` blindly.** models.dev already records the full base. Z.ai is
  `…/api/coding/paas/v4`; adding `/v1` yields a 404. Only a bare host (`https://api.deepseek.com`)
  needs it. This tool gets it right — but if you hand-edit, this is the trap.
- **Grok rewrites `config.toml`.** Switching models in the TUI makes grok normalise the file and
  **strip every comment**. It has also been seen rewriting `[models] default` to the last model
  used. Re-check that line after playing with the model picker.
- **A probe without a real `User-Agent` gets 403.** The WAF in front of `opencode.ai` rejects
  `Python-urllib`, which reads as "key not entitled" when the key is fine. `grok-connect` sends
  a UA; remember it if you roll your own check.
- **Anthropic-protocol providers are not supported yet.** MiniMax's coding plan and friends
  authenticate with `x-api-key`, and `grok-cred` only mints `Authorization: Bearer`.
- **Providers with their own SDK can't be attached** (Google, Anthropic direct, xAI): models.dev
  lists no REST base URL for them, so grok has nothing to call.

## ChatGPT subscription — optional, and against OpenAI's terms

<details>
<summary><b>Read this before expanding.</b></summary>

You can point grok at a ChatGPT Plus/Pro subscription instead of an OpenAI API key. It works —
including tool calling — but it routes through `chatgpt.com/backend-api/codex`, an endpoint
reserved for OpenAI's own Codex client.

> ⚠️ **This breaks OpenAI's terms of service and can get your account suspended.** It is not a
> public API. If you want GPT models in grok for real work, use an OpenAI Platform key
> (`base_url = "https://api.openai.com/v1"`, `api_backend = "responses"`) — that path is
> supported, stable, and legitimate. What follows is documented because the failure modes are
> interesting, not because it is a good idea.

```sh
./install.sh --with-chatgpt
codex login          # or sign in through opencode; the shim reuses that token
grok-connect add chatgpt
```

Two protocol mismatches had to be bridged, and both are worth knowing if you ever wire a client
to a Responses-style backend:

1. **`400 System messages are not allowed.`** Grok serializes the system prompt as an input item
   with `role: "system"`. The Codex backend only accepts it in the top-level `instructions` field.
   The shim hoists it.
2. **One question, four identical requests.** With `store: false` the backend returns
   `response.completed` carrying `output: []` — the text exists only in the streamed deltas. Grok
   builds its assistant message from that final object, sees an empty response, classifies it as a
   retryable server error, and re-sends the *same* payload until the retry budget runs out. The
   shim collects items from `response.output_item.done` and splices them back into `output`.

The model name must be one the ChatGPT plan allows (`gpt-5.6-sol` works; `gpt-5` is rejected).
`grok-cred` starts the shim on demand, so there is nothing to run by hand. Expect one extra
upstream request per session: grok tries HTTP/2 first and falls back to HTTP/1.1.

</details>

## License

MIT. Not affiliated with xAI, OpenAI, Z.ai, DeepSeek, or opencode.
