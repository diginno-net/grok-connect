---
name: connect
description: Cắm hoặc gỡ model provider bên thứ ba cho Grok (GLM/Z.ai, DeepSeek, opencode Zen, Alibaba, ChatGPT OAuth…). Dùng khi người dùng gõ /connect, hỏi "thêm provider", "cắm API key", "đổi sang GLM/DeepSeek", "xài model khác ngoài Grok", hoặc muốn xem provider nào đang có.
argument-hint: "[provider?] [model?]  ·  bỏ trống = liệt kê"
allowed-tools: shell
disable-model-invocation: false
---

# Mục tiêu

Grok không có màn hình chọn provider — `grok login` chỉ đăng nhập xAI, còn provider bên thứ ba
thì phải sửa `config.toml` tay. Skill này thay cho việc đó, qua CLI `grok-connect`.

Khoá **không** được chép vào `config.toml`. Mọi provider trỏ về helper `grok-cred`, đọc kho khoá
của opencode (`~/.local/share/opencode/auth.json`) và Codex (`~/.codex/auth.json`).

# Cách làm

1. **Luôn chạy `grok-connect list` trước** rồi đưa bảng đó cho người dùng xem. Cột `trạng thái`
   nói thẳng cái nào cắm được: `sẵn sàng` · `đã cắm` · `chưa hỗ trợ …`.
2. Người dùng chưa nói rõ muốn provider nào → hỏi 1 câu, kèm gợi ý dựa trên bảng. Đừng tự chọn.
3. Muốn xem có model gì: `grok-connect models <provider>`.
4. Cắm: `grok-connect add <provider> [model…]`. Không truyền model thì lấy 3 model đầu của registry.
   Người dùng nêu tên model cụ thể thì truyền đúng tên đó.
5. Gỡ: `grok-connect remove <provider>`.
6. `add` **tự gọi thật vào endpoint** từng model rồi in HTTP code — đọc kết quả đó cho người dùng.
   Kiểm lại bất cứ lúc nào bằng `grok-connect test <provider>`.
   **`grok models` liệt kê ra KHÔNG chứng minh model chạy được** — base_url sai vẫn hiện trong
   danh sách, tới lúc chat mới ra 404. Chỉ tin cột HTTP của `test`.
7. Model chạy được thì báo người dùng gõ `/model <tên>` hoặc `grok -m <tên>`. Model mới chỉ hiện
   ở session sau.

# Ranh giới phải giữ

- **Không tự ý cắm ChatGPT.** `grok-connect add chatgpt` dùng gói ChatGPT Plus/Pro qua endpoint
  `chatgpt.com/backend-api/codex` — **không phải public API, vi phạm điều khoản OpenAI, rủi ro khoá
  tài khoản**. Chỉ chạy khi người dùng yêu cầu thẳng, và phải nói rõ rủi ro này trước.
- Provider báo `chưa hỗ trợ` thì nói lý do trong bảng, đừng cố lách.
- Provider hết quota / hết số dư là chuyện của tài khoản, không phải lỗi cấu hình — báo đúng như vậy.
- Grok **tự ghi đè `config.toml`** khi đổi model trong TUI và **xoá hết dòng comment**. Sau khi
  người dùng nghịch model picker, kiểm lại `[models] default` xem có bị đổi không.
