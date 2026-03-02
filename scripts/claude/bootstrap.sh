#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/claude/bootstrap.sh --url <url> --api-key <key> [options]

Options:
  --url <url>              Skills Hub URL, e.g. http://127.0.0.1:8000
  --api-key <key>          Skills Hub API Key, e.g. skh_xxx
  --project-dir <path>     Project directory (default: current directory)
  --skills <csv>           Default project skills, e.g. deploy-k8s,code-review
  -h, --help               Show help
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Missing dependency: $1" >&2
    exit 1
  }
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_SCRIPT="$ROOT_DIR/setup-claude.sh"

URL=""
API_KEY=""
PROJECT_DIR="$(pwd)"
SKILLS_CSV=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      [[ $# -ge 2 ]] || { echo "[ERROR] --url requires a value" >&2; exit 1; }
      URL="$2"
      shift 2
      ;;
    --api-key)
      [[ $# -ge 2 ]] || { echo "[ERROR] --api-key requires a value" >&2; exit 1; }
      API_KEY="$2"
      shift 2
      ;;
    --project-dir)
      [[ $# -ge 2 ]] || { echo "[ERROR] --project-dir requires a value" >&2; exit 1; }
      PROJECT_DIR="$2"
      shift 2
      ;;
    --skills)
      [[ $# -ge 2 ]] || { echo "[ERROR] --skills requires a value" >&2; exit 1; }
      SKILLS_CSV="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

[[ -n "$URL" ]] || { echo "[ERROR] --url is required" >&2; exit 1; }
[[ -n "$API_KEY" ]] || { echo "[ERROR] --api-key is required" >&2; exit 1; }
[[ -d "$PROJECT_DIR" ]] || { echo "[ERROR] project dir not found: $PROJECT_DIR" >&2; exit 1; }
[[ -f "$SETUP_SCRIPT" ]] || { echo "[ERROR] setup script not found: $SETUP_SCRIPT" >&2; exit 1; }

require_cmd bash
require_cmd jq

echo "[INFO] Running non-interactive Claude Code setup..."
bash "$SETUP_SCRIPT" \
  --url "$URL" \
  --api-key "$API_KEY" \
  --project-dir "$PROJECT_DIR" \
  --write-project true \
  --non-interactive

if [[ -n "$SKILLS_CSV" ]]; then
  PROJECT_CFG="$PROJECT_DIR/.skills-hub.json"
  if [[ -f "$PROJECT_CFG" ]]; then
    TMP_FILE="$(mktemp)"
    jq --arg csv "$SKILLS_CSV" '
      .skills = ($csv | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0)))
    ' "$PROJECT_CFG" > "$TMP_FILE"
    mv "$TMP_FILE" "$PROJECT_CFG"
    echo "[INFO] Updated default skills in $PROJECT_CFG"
  fi
fi

echo "[INFO] Done."
