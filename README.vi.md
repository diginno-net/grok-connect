# grok-connect

Cắm model provider bên thứ ba vào **Grok Build** (CLI `grok` của xAI) — GLM/Z.ai, DeepSeek,
opencode Zen, Alibaba, hay bất kỳ endpoint OpenAI-compatible nào — mà không phải sửa TOML tay,
và không chép một dòng API key nào vào file config.

[English](README.md) · **Tiếng Việt** · [中文](README.zh.md)

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

## `/connect` ngay trong TUI

![Lệnh /connect liệt kê mọi provider, kiểu xác thực và đã cắm hay chưa](docs/connect-provider-table.png)

Gõ `/connect`, agent tự chạy `grok-connect list`, đọc bảng đó cho bạn nghe rồi hỏi muốn cắm
provider nào — nó không tự chọn thay bạn. *(Skill có bản Anh, Việt, Trung; ảnh chụp bản tiếng Việt.)*

![Agent đề xuất lệnh grok-connect add với đầy đủ model, kèm cảnh báo chỉ HTTP thành công mới tính là chạy được](docs/connect-add-and-verify.png)

Để ý dòng cuối: **chỉ HTTP trả về thành công mới tính là chạy được.** Có mặt trong registry hay
trong `/model` không chứng minh endpoint hoạt động. Model mới xuất hiện từ session grok kế tiếp.

---

## Vì sao có cái này

Grok Build vốn đã là client đa nhà cung cấp — bộ sampler của nó nói được 3 protocol
(`chat_completions`, `responses`, Anthropic `messages`), và khối `[model.*]` cho trỏ tới endpoint
bất kỳ. Cái nó **không** có là đường để dùng chuyện đó:

- `grok login` chỉ đăng nhập **xAI** (OAuth · device code · OIDC · external auth binary).
- Không có `/connect`, không có màn hình chọn provider, không có chỗ dán API key.
- Thêm provider = viết tay 3 khối TOML và phải đúng từng field.

`grok-connect` lấp đúng chỗ đó. Nó đọc registry [models.dev](https://models.dev) để lấy base URL
và danh mục model, tự lấy khoá, ghi config, **rồi gọi thật vào endpoint để chứng minh là chạy được**.

## Gồm những gì

| Thành phần | Việc |
|---|---|
| `grok-connect` | CLI: `list` · `models` · `add` · `test` · `remove`. Ghi/gỡ các khối config. |
| `grok-cred` | Credential helper cắm vào `[auth_provider.*]` của grok. Lấy khoá lúc gọi, nên **không secret nào bị ghi vào `config.toml`**. |
| Skill `/connect` | Chính cái CLI trên, hiện thành slash command trong TUI grok. Có bản Anh, Việt, Trung. |
| `grok-skills-prune` | Cắt danh mục skill của grok xuống còn thứ nó thực sự dùng — xem mục cuối README. |
| `chatgpt-responses-shim` | *Tuỳ chọn, mặc định không cài.* Nối grok với gói ChatGPT qua một endpoint không chính thức — xem mục ở cuối README. |

## Cần có

- [Grok Build](https://x.ai/cli) ≥ 1.0.5 (`grok --version`)
- Python 3.9+
- Khoá từ **một trong hai** nguồn:
  - kho credential của [opencode](https://opencode.ai) (`~/.local/share/opencode/auth.json`) — tự nhận, không phải cấu hình gì
  - biến môi trường — tên do models.dev khai (`DEEPSEEK_API_KEY`, `ZHIPU_API_KEY`, `OPENCODE_API_KEY`…) hoặc `GROK_CRED_<PROVIDER>`

## Cài

```sh
git clone <repo-này> && cd grok-connect
./install.sh                 # script vào ~/.local/bin, skill /connect vào mọi ~/.grok*
SKILL_LANG=vi ./install.sh   # skill bản tiếng Việt (còn có: zh)
```

`install.sh` tự tìm mọi grok home trên máy (`~/.grok`, `~/.grok-100`…) và cài skill vào từng cái.
Đặt `GROK_HOME` nếu chỉ muốn cài vào một profile.

## Dùng

```sh
grok-connect list                              # ai có khoá, cái nào đã cắm
grok-connect models zai-coding-plan            # danh mục model của provider
grok-connect add zai-coding-plan glm-5.2       # cắm (không nêu model = lấy 3 cái đầu)
grok-connect test zai-coding-plan              # kiểm lại bất cứ lúc nào
grok-connect remove zai-coding-plan            # gỡ
```

Hoặc trong grok gõ `/connect` rồi để agent làm.

Model mới chỉ hiện ở session **sau** — rồi dùng `/model <tên>` hoặc `grok -m <tên>`.

## Nó ghi cái gì

Ba khối cho mỗi provider. Để ý: không có khoá ở đâu cả.

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

Grok chạy `grok-cred` trước mỗi lượt cần token, cache trong RAM, và chạy lại khi hết hạn hoặc bị
server từ chối. Token không chạm đĩa. Model gắn auth provider là **BYOK tuyệt đối: session token
xAI của bạn không bao giờ bị gửi sang endpoint bên thứ ba.**

## Kiểm chứng — và vì sao `grok models` không phải bằng chứng

`grok models` chỉ đọc file config. Model có `base_url` sai vẫn hiện đủ trong danh sách; tới lúc
chat mới lòi ra 404. `add` và `test` gọi HTTP thật cho từng model:

| HTTP | Nghĩa |
|---|---|
| 200 | chạy được |
| 401 / 403 | khoá sai hoặc hết hạn · khoá không có quyền với model này |
| **402** | hết số dư — **cấu hình đúng**, nạp tiền là chạy |
| **404** | **sai `base_url` hoặc sai tên model** |
| **429** | hết quota / rate limit — **cấu hình đúng**, chờ reset |

Tách như vậy mới rõ: 402 và 429 là chuyện tài khoản, còn 404 là mình làm sai.

## Mấy cái bẫy nên biết

- **Đừng nối `/v1` một cách máy móc.** models.dev đã ghi base đầy đủ. Z.ai là
  `…/api/coding/paas/v4`, nối thêm `/v1` là 404 ngay. Chỉ host trần
  (`https://api.deepseek.com`) mới cần. Tool này xử đúng rồi — nhưng sửa tay thì dính bẫy này.
- **Khai trùng một bảng là chết cả config — mà im lặng.** TOML cấm khai `[skills]` hay
  `[plugins]` hai lần, và grok gặp config sai thì bỏ **nguyên file** — mất luôn model provider.
  Không báo gì cả; chỉ `grok inspect --json` mới lộ `configSources` có `"note": "parse error"`.
  `grok-connect` thà không ghi còn hơn tạo ra tình trạng đó, nhưng sửa tay thì nhớ **gộp vào
  bảng có sẵn**, đừng thêm bảng thứ hai.
- **Grok tự ghi đè `config.toml`.** Đổi model trong TUI là nó normalise lại file và **xoá sạch
  comment**. Có lần nó còn tự đổi `[models] default` thành model vừa dùng. Nghịch model picker
  xong nhớ liếc lại dòng đó.
- **Probe thiếu `User-Agent` thật thì ăn 403.** WAF trước `opencode.ai` chặn `Python-urllib`,
  đọc lên thành "khoá không có quyền" trong khi khoá không sao cả. `grok-connect` có gửi UA — tự
  viết script kiểm thì nhớ chuyện này.
- **Provider dùng protocol Anthropic chưa hỗ trợ.** Gói coding của MiniMax và tương tự xác thực
  bằng `x-api-key`, còn `grok-cred` chỉ mint được `Authorization: Bearer`.
- **Provider có SDK riêng thì không cắm được** (Google, Anthropic trực tiếp, xAI): models.dev
  không khai base URL REST cho chúng, grok không có gì để gọi.

## Gói ChatGPT — tuỳ chọn, endpoint không chính thức

<details>
<summary><b>Mở ra xem cách cài và hai chỗ lệch protocol phải bắc cầu.</b></summary>

Có thể cho grok dùng gói ChatGPT Plus/Pro thay vì API key OpenAI. Nó chạy được, kể cả tool
calling, giống cách opencode và mấy CLI khác cho đăng nhập ChatGPT. Đường đi qua
`chatgpt.com/backend-api/codex`.

> **Đó là endpoint nội bộ, không phải public API.** Không có cam kết ổn định nào: shape của
> request/response đổi lúc nào cũng được, và shim này sẽ gãy theo. Chuyện dùng từ client bên thứ
> ba có hợp với thoả thuận giữa bạn và OpenAI hay không là việc bạn tự cân, README này không
> phán. Chạy production thì key OpenAI Platform (`base_url = "https://api.openai.com/v1"`,
> `api_backend = "responses"`) mới là đường có tài liệu, có version, có hỗ trợ.

```sh
./install.sh --with-chatgpt
codex login          # hoặc đăng nhập qua opencode; shim dùng lại token đó
grok-connect add chatgpt
```

Có hai chỗ lệch protocol phải bắc cầu, và cả hai đều đáng biết nếu bạn từng nối client vào một
backend kiểu Responses:

1. **`400 System messages are not allowed.`** Grok serialize system prompt thành input item
   `role: "system"`. Backend Codex chỉ nhận nó ở field `instructions` cấp cao nhất. Shim nhấc lên.
2. **Một câu hỏi, bốn request giống hệt nhau.** Với `store: false`, backend trả `response.completed`
   kèm `output: []` — chữ chỉ nằm trong các delta được stream. Grok dựng câu trả lời từ chính cái
   object cuối đó, thấy rỗng, xếp thành lỗi server retry được, rồi gửi lại *đúng payload cũ* cho
   tới khi hết hạn mức retry. Shim gom item từ `response.output_item.done` rồi nhét ngược vào
   `output`.

3. **`serialization error: unknown variant 'keepalive'`.** Lúc model nghĩ lâu, backend chèn
   nhịp tim SSE `keepalive`. Grok parse stream bằng enum đóng nên gặp event lạ là lỗi **không
   retry được**, chết luôn cả lượt. Shim chỉ chuyển tiếp event `response.*` (và `error`), bỏ
   phần nhiễu vận chuyển.

Tên model phải là cái gói ChatGPT cho phép (`gpt-5.6-sol` chạy; `gpt-5` bị từ chối). `grok-cred`
tự bật shim khi cần nên không phải chạy tay gì. Chấp nhận thêm 1 request/session: grok thử HTTP/2
trước rồi mới fallback HTTP/1.1.

</details>

## Cộng đồng

Có câu hỏi, cắm provider mãi không lên, hay dựng được setup hay ho — mang qua
**[OpenCode Vietnam](https://www.facebook.com/groups/opencode.io.vn)** — nhóm Facebook của anh em
ghép mấy con AI coding CLI (opencode, Grok Build, Codex, Claude Code) vào việc thật.

Báo lỗi và pull request thì để ở issue tracker; nhóm dành cho mấy chuyện lộn xộn kiểu
"có ai nối được X với Y chưa".

## Kèm theo: `grok-skills-prune`

Không liên quan provider — nhưng nằm trong repo này vì nó chữa cái cách *còn lại* làm chết phiên grok.

Grok gom skill từ `~/.grok*/skills`, `~/.agents/skills`, `~/.claude/skills` và plugin (compat
Claude Code, không tắt được), liệt kê **tất cả** vào một `<system-reminder>`, rồi **chèn lại danh
mục đó mỗi lượt gọi model** — và giữ luôn mọi bản sao trong lịch sử hội thoại.

Đo trên máy có kho skill lớn:

```
460 skill = 145 KB = ~37.000 token mỗi lượt gọi model
72 bản sao trong 1 phiên = 10,4 MB = 98% toàn bộ lịch sử
ba phiên vượt 3M token và không cứu được
```

Auto-compact không cứu nổi: request compact vác đúng đống lịch sử đó nên cũng bị từ chối. Còn
provider bên thứ ba báo lỗi vượt cửa sổ **bên trong SSE stream**, không có HTTP status, nên grok
tưởng retry được và gửi lại y hệt payload quá khổ 15 lần — khoảng 9 phút đứng im rồi mới lỗi.

```sh
grok-skills-prune            # xem sẽ giữ/chặn gì, không ghi
grok-skills-prune --apply    # ghi [skills] ignore vào mọi grok home
```

Nó giữ những skill grok **thực sự đã mở** (đếm lượt đọc `<skill>/SKILL.md` trong lịch sử phiên —
grok không có tool `skill`, đọc file *chính là* cách nó nạp skill) và chặn phần còn lại. Không di
chuyển hay sửa file skill nào; chỉ ghi `[skills] ignore`, nên kho skill của bạn vẫn là nguồn duy nhất.

**Sổ đăng ký lượt dùng (tuỳ chọn).** Lịch sử riêng của grok sẽ hẹp nếu grok mới vào hệ của bạn.
Trỏ tool sang một bảng đã theo dõi lượt dùng skill trên nhiều tool:

```json
// ~/.config/grok-connect/registry.json
{"base_token": "…", "table_id": "tbl…", "keep_status": "Dùng thường xuyên",
 "name_field": "Skill", "status_field": "Trạng thái"}
```

Cần `lark-cli`. Không có file, không có CLI, hoặc Base không gọi được — tool tự lùi về dùng lịch
sử grok, không báo lỗi ầm ĩ. Thêm skill mới thì chạy lại.

## Giấy phép

MIT. Không liên kết với xAI, OpenAI, Z.ai, DeepSeek hay opencode.
