#!/usr/bin/env bash
set -euo pipefail

# Skills Hub - Claude Code 集成配置脚本
# 自动配置 Hook + MCP Server + 环境变量

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo -e "${BOLD}=== Skills Hub - Claude Code 集成配置 ===${NC}"
echo ""

# --- 1. 收集参数 ---
read -rp "Skills Hub URL (例如 http://localhost:8000): " SKILLS_HUB_URL
SKILLS_HUB_URL="${SKILLS_HUB_URL%/}"  # 去掉尾部斜杠

if [[ -z "$SKILLS_HUB_URL" ]]; then
  error "URL 不能为空"
fi

read -rp "API Key: " API_KEY
if [[ -z "$API_KEY" ]]; then
  error "API Key 不能为空"
fi

echo ""
info "配置参数："
echo "  URL:     $SKILLS_HUB_URL"
echo "  API Key: ${API_KEY:0:8}..."
echo ""

# --- 2. 验证连接 ---
info "验证 API 连接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $API_KEY" \
  "${SKILLS_HUB_URL}/plugin/skills" 2>/dev/null || true)

if [[ "$HTTP_CODE" == "200" ]]; then
  info "API 连接成功"
elif [[ "$HTTP_CODE" == "401" || "$HTTP_CODE" == "403" ]]; then
  error "API Key 无效 (HTTP $HTTP_CODE)"
else
  warn "无法验证 API (HTTP $HTTP_CODE)，继续配置..."
fi

# --- 3. 创建 Hook 脚本 ---
HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/fetch-skills.sh"

info "创建 Hook 脚本: $HOOK_FILE"
mkdir -p "$HOOK_DIR"

cat > "$HOOK_FILE" << 'HOOKEOF'
#!/usr/bin/env bash
# Skills Hub - fetch skills on user prompt submit
SKILLS_HUB_URL="${SKILLS_HUB_URL:-http://localhost:8000}"
SKILLS_HUB_API_KEY="${SKILLS_HUB_API_KEY:-}"

if [[ -z "$SKILLS_HUB_API_KEY" ]]; then
  exit 0
fi

INPUT=$(cat)
USER_MSG=$(echo "$INPUT" | jq -r '.messages[-1].content // empty' 2>/dev/null)

if [[ -z "$USER_MSG" ]]; then
  exit 0
fi

RESPONSE=$(curl -s --max-time 5 \
  -H "Authorization: Bearer $SKILLS_HUB_API_KEY" \
  -H "Content-Type: application/json" \
  "${SKILLS_HUB_URL}/plugin/match" \
  -d "{\"query\": \"$USER_MSG\"}" 2>/dev/null)

SKILL=$(echo "$RESPONSE" | jq -r '.skill // empty' 2>/dev/null)

if [[ -n "$SKILL" ]]; then
  jq -n --arg s "$SKILL" '{"instructions": $s}'
else
  echo '{}'
fi
HOOKEOF

chmod +x "$HOOK_FILE"

# --- 4. 更新 ~/.claude/settings.json (Hook 配置) ---
SETTINGS_FILE="$HOME/.claude/settings.json"
info "更新 Hook 配置: $SETTINGS_FILE"

if [[ -f "$SETTINGS_FILE" ]]; then
  SETTINGS=$(cat "$SETTINGS_FILE")
else
  SETTINGS='{}'
fi

# 使用 jq 合并 hook 配置
SETTINGS=$(echo "$SETTINGS" | jq '
  .hooks //= {} |
  .hooks.UserPromptSubmit //= [] |
  (if (.hooks.UserPromptSubmit | map(select(.command | contains("fetch-skills"))) | length) == 0
   then .hooks.UserPromptSubmit += [{
     "command": "bash ~/.claude/hooks/fetch-skills.sh",
     "timeout": 10000
   }]
   else . end)
')

echo "$SETTINGS" | jq '.' > "$SETTINGS_FILE"

# --- 5. 更新 ~/.claude.json (MCP Server 配置) ---
CLAUDE_JSON="$HOME/.claude.json"
info "更新 MCP 配置: $CLAUDE_JSON"

if [[ -f "$CLAUDE_JSON" ]]; then
  CLAUDE_CFG=$(cat "$CLAUDE_JSON")
else
  CLAUDE_CFG='{}'
fi

MCP_SERVER_URL="${SKILLS_HUB_URL}/mcp"

CLAUDE_CFG=$(echo "$CLAUDE_CFG" | jq --arg url "$MCP_SERVER_URL" --arg key "$API_KEY" '
  .mcpServers //= {} |
  .mcpServers["skills-hub"] = {
    "type": "sse",
    "url": $url,
    "headers": {
      "Authorization": ("Bearer " + $key)
    }
  }
')

echo "$CLAUDE_CFG" | jq '.' > "$CLAUDE_JSON"

# --- 6. 设置环境变量 ---
info "设置环境变量..."

# 检测 shell 配置文件
if [[ -n "${ZSH_VERSION:-}" ]] || [[ "$SHELL" == */zsh ]]; then
  RC_FILE="$HOME/.zshrc"
else
  RC_FILE="$HOME/.bashrc"
fi

# 移除旧的 Skills Hub 环境变量（如果存在）
if [[ -f "$RC_FILE" ]]; then
  sed -i '/^# Skills Hub$/d; /^export SKILLS_HUB_URL=/d; /^export SKILLS_HUB_API_KEY=/d' "$RC_FILE"
fi

cat >> "$RC_FILE" << EOF
# Skills Hub
export SKILLS_HUB_URL="${SKILLS_HUB_URL}"
export SKILLS_HUB_API_KEY="${API_KEY}"
EOF

info "环境变量已写入 $RC_FILE"

# --- 7. 完成 ---
echo ""
echo -e "${BOLD}${GREEN}=== 配置完成！ ===${NC}"
echo ""
echo "已完成以下配置："
echo "  1. Hook 脚本:  $HOOK_FILE"
echo "  2. Hook 配置:  $SETTINGS_FILE"
echo "  3. MCP 配置:   $CLAUDE_JSON"
echo "  4. 环境变量:   $RC_FILE"
echo ""
echo -e "${YELLOW}请执行以下命令使环境变量生效：${NC}"
echo "  source $RC_FILE"
echo ""
echo "然后重启 Claude Code 即可使用 Skills Hub 集成。"
