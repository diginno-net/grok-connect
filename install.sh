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
install -m 755 "$here/bin/grok-skills-prune" "$BIN_DIR/grok-skills-prune"
echo "installed: $BIN_DIR/{grok-cred,grok-connect,grok-skills-prune}"

if [[ $WITH_CHATGPT == 1 ]]; then
  install -m 755 "$here/bin/chatgpt-responses-shim" "$BIN_DIR/chatgpt-responses-shim"
  echo "installed: $BIN_DIR/chatgpt-responses-shim"
  echo "NOTE: the ChatGPT path talks to chatgpt.com/backend-api/codex, an internal"
  echo "      endpoint with no stability guarantee - it can change without notice"
  echo "      and this shim will break when it does. See the README."
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
