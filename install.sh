#!/usr/bin/env bash
# Install grok-connect. The ChatGPT path is NOT installed by default (see README).
set -euo pipefail

BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
WITH_CHATGPT=0
[[ "${1:-}" == "--with-chatgpt" ]] && WITH_CHATGPT=1

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$BIN_DIR"

install -m 755 "$here/bin/grok-cred"    "$BIN_DIR/grok-cred"
install -m 755 "$here/bin/grok-connect" "$BIN_DIR/grok-connect"
echo "installed: $BIN_DIR/{grok-cred,grok-connect}"

if [[ $WITH_CHATGPT == 1 ]]; then
  install -m 755 "$here/bin/chatgpt-responses-shim" "$BIN_DIR/chatgpt-responses-shim"
  echo "installed: $BIN_DIR/chatgpt-responses-shim"
  echo "WARNING: the ChatGPT path uses your ChatGPT subscription through an endpoint"
  echo "         reserved for OpenAI's own Codex client. It violates OpenAI's terms"
  echo "         and can get your account suspended. You installed it on purpose."
fi

# Install the /connect skill into every grok home found (SKILL_LANG=en|vi|zh)
homes=()
if [[ -n "${GROK_HOME:-}" ]]; then homes+=("$GROK_HOME"); else
  for d in "$HOME"/.grok "$HOME"/.grok-*; do [[ -d "$d" ]] && homes+=("$d"); done
fi
for h in "${homes[@]:-}"; do
  [[ -d "$h" ]] || continue
  mkdir -p "$h/skills/connect"
  src="$here/skill/connect/SKILL.md"
  [[ "${SKILL_LANG:-en}" != "en" && -f "$here/skill/connect/SKILL.${SKILL_LANG}.md" ]] \
    && src="$here/skill/connect/SKILL.${SKILL_LANG}.md"
  install -m 644 "$src" "$h/skills/connect/SKILL.md"
  echo "installed skill: $h/skills/connect/SKILL.md"
done

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "NOTE: $BIN_DIR is not on PATH — add it to your shell profile." ;;
esac

echo
echo "Next: grok-connect list"
