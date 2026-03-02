#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/claude/smoke-test.sh [--project-dir <path>]

Reads config from:
  1) <project-dir>/.skills-hub.json
  2) env: SKILLS_HUB_URL + SKILLS_HUB_API_KEY
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Missing dependency: $1" >&2
    exit 1
  }
}

PROJECT_DIR="$(pwd)"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir)
      [[ $# -ge 2 ]] || { echo "[ERROR] --project-dir requires a value" >&2; exit 1; }
      PROJECT_DIR="$2"
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

require_cmd curl
require_cmd jq

CFG="$PROJECT_DIR/.skills-hub.json"
URL=""
API_KEY=""
SKILLS='[]'

if [[ -f "$CFG" ]]; then
  URL="$(jq -r '.url // empty' "$CFG")"
  API_KEY="$(jq -r '.api_key // empty' "$CFG")"
  SKILLS="$(jq -rc '.skills // []' "$CFG")"
fi

URL="${URL:-${SKILLS_HUB_URL:-}}"
API_KEY="${API_KEY:-${SKILLS_HUB_API_KEY:-}}"
URL="${URL%/}"

[[ -n "$URL" ]] || { echo "[ERROR] Missing URL (.skills-hub.json or SKILLS_HUB_URL)" >&2; exit 1; }
[[ -n "$API_KEY" ]] || { echo "[ERROR] Missing API key (.skills-hub.json or SKILLS_HUB_API_KEY)" >&2; exit 1; }

echo "[INFO] Testing catalog endpoint..."
CATALOG="$(curl -sS --max-time 10 -H "Authorization: Bearer $API_KEY" "$URL/api/v1/skills/catalog")"

if ! echo "$CATALOG" | jq -e '.skills and (.skills | type == "array")' >/dev/null; then
  echo "[ERROR] Catalog response invalid:" >&2
  echo "$CATALOG" >&2
  exit 1
fi

COUNT="$(echo "$CATALOG" | jq '.skills | length')"
NAMES="$(echo "$CATALOG" | jq -r '.skills | map(.name) | join(", ")')"
echo "[INFO] Catalog OK. Subscribed skills: $COUNT"
if [[ -n "$NAMES" ]]; then
  echo "[INFO] Names: $NAMES"
fi

if [[ "$SKILLS" != "[]" ]]; then
  echo "[INFO] Testing resolve endpoint with project default skills..."
  RESOLVE_PAYLOAD="$(jq -nc --argjson skills "$SKILLS" '{skills: $skills}')"
  RESOLVE="$(echo "$RESOLVE_PAYLOAD" | curl -sS --max-time 12 -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" "$URL/api/v1/skills/resolve" -d @-)"
  if ! echo "$RESOLVE" | jq -e '.skills and (.skills | type == "array")' >/dev/null; then
    echo "[ERROR] Resolve response invalid:" >&2
    echo "$RESOLVE" >&2
    exit 1
  fi
  RCOUNT="$(echo "$RESOLVE" | jq '.skills | length')"
  echo "[INFO] Resolve OK. Returned skills: $RCOUNT"
fi

echo "[INFO] Smoke test passed."
