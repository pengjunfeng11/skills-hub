#!/usr/bin/env bash
set -euo pipefail

# Skills Hub - Claude Code 集成配置脚本
# 自动配置 Hook + MCP Server + 环境变量 + 项目级配置

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  bash setup-claude.sh [options]

Options:
  --url <url>              Skills Hub URL, e.g. http://127.0.0.1:8000
  --api-key <key>          Skills Hub API Key, e.g. skh_xxx
  --project-dir <path>     Project directory for writing .skills-hub.json
  --write-project <bool>   Write .skills-hub.json (true/false), default: true
  --non-interactive        Fail if required params are missing, no prompts
  -h, --help               Show help

Env fallback:
  SKILLS_HUB_URL
  SKILLS_HUB_API_KEY
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "缺少依赖命令: $1"
}

parse_bool() {
  case "${1:-}" in
    1|true|TRUE|True|yes|YES|Yes|y|Y|on|ON) echo "true" ;;
    0|false|FALSE|False|no|NO|No|n|N|off|OFF) echo "false" ;;
    *) error "无效布尔值: $1（请使用 true/false）" ;;
  esac
}

echo -e "${BOLD}=== Skills Hub - Claude Code 集成配置 ===${NC}"
echo ""

# --- 0. 依赖检查 ---
require_cmd curl
require_cmd jq

# --- 1. 参数解析 ---
NON_INTERACTIVE="false"
SKILLS_HUB_URL="${SKILLS_HUB_URL:-}"
API_KEY="${SKILLS_HUB_API_KEY:-}"
USE_PROJECT_CFG="true"
PROJECT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      [[ $# -ge 2 ]] || error "--url 需要参数"
      SKILLS_HUB_URL="$2"
      shift 2
      ;;
    --api-key)
      [[ $# -ge 2 ]] || error "--api-key 需要参数"
      API_KEY="$2"
      shift 2
      ;;
    --project-dir)
      [[ $# -ge 2 ]] || error "--project-dir 需要参数"
      PROJECT_DIR="$2"
      shift 2
      ;;
    --write-project)
      [[ $# -ge 2 ]] || error "--write-project 需要参数"
      USE_PROJECT_CFG="$(parse_bool "$2")"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      error "未知参数: $1（使用 --help 查看帮助）"
      ;;
  esac
done

# --- 1. 收集参数 ---
if [[ -z "$SKILLS_HUB_URL" ]]; then
  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    error "缺少 --url 或环境变量 SKILLS_HUB_URL"
  fi
  read -rp "Skills Hub URL/IP (例如 http://127.0.0.1:8000): " SKILLS_HUB_URL
fi
SKILLS_HUB_URL="${SKILLS_HUB_URL%/}"  # 去掉尾部斜杠

if [[ -z "$SKILLS_HUB_URL" ]]; then
  error "URL 不能为空"
fi

if [[ -z "$API_KEY" ]]; then
  if [[ "$NON_INTERACTIVE" == "true" ]]; then
    error "缺少 --api-key 或环境变量 SKILLS_HUB_API_KEY"
  fi
  read -rp "API Key (skh_...): " API_KEY
fi
if [[ -z "$API_KEY" ]]; then
  error "API Key 不能为空"
fi

if [[ "$NON_INTERACTIVE" != "true" ]]; then
  echo ""
  read -rp "是否写入当前项目配置文件 .skills-hub.json? [Y/n]: " ans
  if [[ -n "$ans" ]]; then
    USE_PROJECT_CFG="$(parse_bool "$ans")"
  fi
fi

if [[ "$USE_PROJECT_CFG" == "true" ]]; then
  if [[ -z "$PROJECT_DIR" ]]; then
    if [[ "$NON_INTERACTIVE" == "true" ]]; then
      PROJECT_DIR="$(pwd)"
    else
      read -rp "项目目录 (默认: $(pwd)): " PROJECT_DIR
      PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
    fi
  fi
  if [[ ! -d "$PROJECT_DIR" ]]; then
    error "项目目录不存在: $PROJECT_DIR"
  fi
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
  "${SKILLS_HUB_URL}/api/v1/skills/catalog" 2>/dev/null || true)

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
# Skills Hub - fetch project scoped skills on user prompt submit
set -euo pipefail

INPUT="$(cat)"
USER_MSG="$(echo "$INPUT" | jq -r '.messages[-1].content // empty' 2>/dev/null || true)"
CWD="$(echo "$INPUT" | jq -r '.cwd // .workspace.cwd // empty' 2>/dev/null || true)"
CWD="${CWD:-$(pwd)}"

find_project_config() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/.skills-hub.json" ]]; then
      echo "$dir/.skills-hub.json"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

PROJECT_CFG="$(find_project_config "$CWD" || true)"
CFG_URL=""
CFG_KEY=""
CFG_SKILLS=""

if [[ -n "$PROJECT_CFG" ]]; then
  CFG_URL="$(jq -r '.url // empty' "$PROJECT_CFG" 2>/dev/null || true)"
  CFG_KEY="$(jq -r '.api_key // empty' "$PROJECT_CFG" 2>/dev/null || true)"
  CFG_SKILLS="$(jq -rc '.skills // []' "$PROJECT_CFG" 2>/dev/null || echo '[]')"
fi

SKILLS_HUB_URL="${CFG_URL:-${SKILLS_HUB_URL:-http://localhost:8000}}"
SKILLS_HUB_API_KEY="${CFG_KEY:-${SKILLS_HUB_API_KEY:-}}"
SKILLS_HUB_URL="${SKILLS_HUB_URL%/}"

if [[ -z "$SKILLS_HUB_API_KEY" ]]; then
  echo '{}'
  exit 0
fi

# 先拿订阅目录（只返回当前可用 skills）
CATALOG_JSON="$(curl -s --max-time 8 \
  -H "Authorization: Bearer $SKILLS_HUB_API_KEY" \
  "$SKILLS_HUB_URL/api/v1/skills/catalog" 2>/dev/null || true)"

AVAILABLE_SKILLS="$(echo "$CATALOG_JSON" | jq -rc '.skills // []' 2>/dev/null || echo '[]')"

# 从用户消息中提取 @skill-name
MENTIONED_SKILLS="$(printf '%s' "$USER_MSG" | grep -Eo '@[a-z0-9][a-z0-9-]*' | sed 's/^@//' | sort -u || true)"

# 优先级：消息中提到的 skill > 项目配置 skills
REQ_SKILLS='[]'
if [[ -n "$MENTIONED_SKILLS" ]]; then
  REQ_SKILLS="$(printf '%s\n' "$MENTIONED_SKILLS" | jq -R . | jq -sc .)"
elif [[ -n "$CFG_SKILLS" && "$CFG_SKILLS" != "[]" ]]; then
  REQ_SKILLS="$CFG_SKILLS"
fi

# 若无明确请求，只返回目录提示，避免每次都注入大量内容
if [[ "$REQ_SKILLS" == "[]" ]]; then
  SKILL_LIST="$(echo "$AVAILABLE_SKILLS" | jq -r 'map(.name) | join(", ")' 2>/dev/null || true)"
  if [[ -z "$SKILL_LIST" ]]; then
    echo '{}'
    exit 0
  fi
  jq -n --arg s "[Skills Hub] 当前项目可用 skills: $SKILL_LIST。若要加载某个 skill，请在消息中使用 @skill-name。" '{"instructions": $s}'
  exit 0
fi

# 只保留 catalog 中可用的 skill，避免无效请求
FILTERED_REQ="$(jq -nc --argjson req "$REQ_SKILLS" --argjson available "$AVAILABLE_SKILLS" '
  [ $req[] as $r | select(($available | map(.name) | index($r)) != null) ] | unique
')"

if [[ "$FILTERED_REQ" == "[]" ]]; then
  jq -n --arg s "[Skills Hub] 请求的 skills 不在当前项目可用订阅内。请先订阅后再使用。" '{"instructions": $s}'
  exit 0
fi

RESOLVE_JSON="$(jq -nc --argjson arr "$FILTERED_REQ" '{skills: $arr}' | \
  curl -s --max-time 12 \
    -H "Authorization: Bearer $SKILLS_HUB_API_KEY" \
    -H "Content-Type: application/json" \
    "$SKILLS_HUB_URL/api/v1/skills/resolve" \
    -d @- 2>/dev/null || true)"

INSTRUCTIONS="$(echo "$RESOLVE_JSON" | jq -r '
  .skills // [] |
  map("## Skill: \(.name)@\(.version)\n\(.content)") |
  join("\n\n---\n\n")
' 2>/dev/null || true)"

if [[ -n "$INSTRUCTIONS" ]]; then
  jq -n --arg s "$INSTRUCTIONS" '{"instructions": $s}'
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
  TMP_FILE="$(mktemp)"
  grep -vE '^(# Skills Hub|export SKILLS_HUB_URL=.*|export SKILLS_HUB_API_KEY=.*)$' "$RC_FILE" > "$TMP_FILE" || true
  mv "$TMP_FILE" "$RC_FILE"
fi

cat >> "$RC_FILE" << EOF
# Skills Hub
export SKILLS_HUB_URL="${SKILLS_HUB_URL}"
export SKILLS_HUB_API_KEY="${API_KEY}"
EOF

info "环境变量已写入 $RC_FILE"

# --- 6.1 可选：写入项目级配置 ---
if [[ "$USE_PROJECT_CFG" == "true" ]]; then
  PROJECT_CFG_FILE="$PROJECT_DIR/.skills-hub.json"
  cat > "$PROJECT_CFG_FILE" << EOF
{
  "url": "${SKILLS_HUB_URL}",
  "api_key": "${API_KEY}",
  "skills": []
}
EOF
  info "项目配置已写入: $PROJECT_CFG_FILE"
  info "你可以在 skills 数组中填入项目默认技能，例如: [\"deploy-k8s\", \"code-review\"]"
fi

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
