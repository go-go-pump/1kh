#!/bin/bash
#
# ThousandHand (KH) - Filesystem-based Claude workflow orchestration
#
# Usage:
#   kh init                    Initialize .kh structure in current directory
#   kh add "name"              Add draft from stdin (supports multi-line)
#   kh status                  Show current queue status + active phase
#   kh view "name"             View a task file and its metadata
#   kh prioritize "name" <n>   Set task priority (lower = first)
#
#   kh run                     Process all drafts (single Opus session per item)
#   kh logs                    Live-tail active Claude session
#   kh watch                   Continuous monitoring mode
#   kh stop                    Stop a running watch/run (from another terminal)
#
#   kh demote "name"           Move task back to draft (redo from scratch)
#   kh promote "name"          Manually advance task to complete
#   kh resume "name"           Resume a failed Claude session from checkpoint
#   kh remove "name"           Permanently remove an item and its files
#
# Based on Kanban Utility (KU) — optimized for 1KH v3 architecture.
# Sources:
#   - https://docs.anthropic.com/en/docs/claude-code/cli-usage
#   - ARCH_V3.md, EXECUTOR_STANDARDS.md, GROOMING_STANDARDS

set -euo pipefail

# KH_HOME = where the thousandhand package lives (for templates/defaults)
# Resolve symlinks (npm link creates symlinks in global bin)
_KH_SCRIPT="${BASH_SOURCE[0]}"
while [ -L "$_KH_SCRIPT" ]; do
  _KH_DIR="$(cd "$(dirname "$_KH_SCRIPT")" && pwd)"
  _KH_SCRIPT="$(readlink "$_KH_SCRIPT")"
  [[ "$_KH_SCRIPT" != /* ]] && _KH_SCRIPT="$_KH_DIR/$_KH_SCRIPT"
done
KH_HOME="$(cd "$(dirname "$_KH_SCRIPT")/.." && pwd)"
KH_TEMPLATES="${KH_HOME}/templates"
KH_DEFAULTS="${KH_HOME}/defaults"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Helpers ---

success() { echo -e "${GREEN}✓${NC} $*"; }
warn()    { echo -e "${YELLOW}⟲${NC} $*"; }
error()   { echo -e "${RED}✗${NC} $*"; }
header()  { echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"; }

to_safe_name() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-'
}

to_feature_name() {
  echo "$1" | tr '-' '_' | tr '[:lower:]' '[:upper:]'
}

# Generic state update — replaces 5 separate functions from KU
update_item() {
  local id="$1" field="$2" value="$3"
  local temp_file timestamp
  temp_file=$(mktemp)
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "$id" --arg field "$field" --arg val "$value" --arg ts "$timestamp" \
     '(.items[] | select(.id == $id))[$field] = $val | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
}

# Numeric update (for tokens — needs --argjson)
update_item_json() {
  local id="$1" jq_expr="$2"
  local temp_file timestamp
  temp_file=$(mktemp)
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "$id" --arg ts "$timestamp" \
     "(.items[] | select(.id == \$id)) | ${jq_expr} | .last_updated = \$ts" \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE" 2>/dev/null || true
}

update_global() {
  local field="$1" value="$2"
  local temp_file timestamp
  temp_file=$(mktemp)
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg field "$field" --arg val "$value" --arg ts "$timestamp" \
     '.[$field] = $val | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
}

clear_global() {
  local field="$1"
  local temp_file timestamp
  temp_file=$(mktemp)
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg field "$field" --arg ts "$timestamp" \
     '.[$field] = null | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
}

# --- Signal handling ---

cleanup() {
  echo ""
  echo -e "${YELLOW}[KH] Caught interrupt — shutting down...${NC}"
  stop_phase_monitor 2>/dev/null || true
  [[ -n "${KH_DIR:-}" ]] && rm -f "${KH_DIR}/STOP"
  kill -- -$$ 2>/dev/null || true
  exit 130
}
trap cleanup SIGINT SIGTERM

check_stop_sentinel() {
  if [[ -n "${KH_DIR:-}" && -f "${KH_DIR}/STOP" ]]; then
    echo -e "${YELLOW}[KH] Stop sentinel detected — halting.${NC}"
    rm -f "${KH_DIR}/STOP"
    exit 0
  fi
}

# --- Path resolution ---

find_kh_dir() {
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    [[ -d "$dir/.kh" ]] && echo "$dir/.kh" && return 0
    dir="$(dirname "$dir")"
  done
  return 1
}

resolve_paths() {
  KH_DIR=$(find_kh_dir) || {
    error "No .kh/ directory found. Run 'kh init' first."
    exit 1
  }
  CONFIG_FILE="${KH_DIR}/config.json"
  STATE_FILE="${KH_DIR}/state.json"
  LOG_FILE="${KH_DIR}/kh.log"
  DRAFT_DIR="${KH_DIR}/draft"
  DEV_DIR="${KH_DIR}/developing"
  COMPLETE_DIR="${KH_DIR}/complete"
}

load_config() {
  resolve_paths
  [[ -f "$CONFIG_FILE" ]] || { error "config.json not found. Run 'kh init' first."; exit 1; }

  # Validate config is valid JSON
  jq empty "$CONFIG_FILE" 2>/dev/null || { error "config.json is empty or invalid JSON. Run 'kh init' to recreate."; exit 1; }

  local raw_root
  raw_root=$(jq -r '.project_root' "$CONFIG_FILE")
  if [[ "$raw_root" == /* ]]; then
    PROJECT_ROOT="$raw_root"
  else
    PROJECT_ROOT="$(cd "${KH_DIR}/.." && cd "$raw_root" && pwd)"
  fi

  CLAUDE_CONTEXT=$(jq -r '.claude_context_path' "$CONFIG_FILE")
  DOCS_PATH="${PROJECT_ROOT}/$(jq -r '.docs_path' "$CONFIG_FILE")"
  HANDOFFS_PATH="${PROJECT_ROOT}/$(jq -r '.handoffs_path' "$CONFIG_FILE")"
  MODEL=$(jq -r '.model // "opus"' "$CONFIG_FILE")
  [[ -z "$MODEL" || "$MODEL" == "null" ]] && MODEL="opus"
  POLL_INTERVAL=$(jq -r '.polling_interval_seconds' "$CONFIG_FILE")
}

# --- Logging ---

log() {
  local level="$1"; shift
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  [[ -n "${LOG_FILE:-}" ]] && echo "[$timestamp] [$level] $*" >> "$LOG_FILE"
  case "$level" in
    INFO)  echo -e "${GREEN}[$level]${NC} $*" ;;
    WARN)  echo -e "${YELLOW}[$level]${NC} $*" ;;
    ERROR) echo -e "${RED}[$level]${NC} $*" ;;
    *)     echo "[$level] $*" ;;
  esac
}

# --- Template generation ---

generate_grooming_standards() {
  local kh_dir="$1" project_root="$2"
  local config_file="${kh_dir}/config.json"
  local template_dir="${kh_dir}/templates"
  local output_file="${template_dir}/GROOMING_STANDARDS.md"

  mkdir -p "$template_dir"
  cp "${KH_TEMPLATES}/MASTER_GROOMING_STANDARDS.md" "$output_file"

  local found_docs=()
  while IFS= read -r doc; do
    [[ -f "${project_root}/${doc}" ]] && found_docs+=("$doc")
  done < <(jq -r '.known_docs[]' "$config_file" 2>/dev/null)

  {
    echo ""; echo "---"; echo ""
    echo "## Project Context"
    echo ""
    echo "> These project docs were selected for reference during grooming and updates."
    echo ""
    if [[ ${#found_docs[@]} -gt 0 ]]; then
      for doc in "${found_docs[@]}"; do echo "- \`${doc}\`"; done
    else
      echo "- _(no project docs selected — re-run \`kh init\` to choose docs)_"
    fi
  } >> "$output_file"
}

generate_local_delivery_template() {
  local kh_dir="$1" project_root="$2"
  local config_file="${kh_dir}/config.json"
  local template_dir="${kh_dir}/templates"
  local output_file="${template_dir}/DELIVERY_HANDOFF_TEMPLATE.md"

  mkdir -p "$template_dir"
  cp "${KH_TEMPLATES}/MASTER_DELIVERY_HANDOFF_TEMPLATE.md" "$output_file"

  local doc_rows="" found_any=false
  while IFS= read -r doc; do
    if [[ -f "${project_root}/${doc}" ]]; then
      found_any=true
      local doc_basename guidance
      doc_basename=$(basename "$doc")
      case "$doc_basename" in
        PRIMER.md)                  guidance="Update current focus/state if project direction changed" ;;
        TECH_STACK.md)              guidance="Add new dependencies or tools introduced" ;;
        SETUP_GUIDE.md)             guidance="Update setup steps if new env vars or services added" ;;
        ARCHITECTURE_STATUS.md)     guidance="Add/update component descriptions and status" ;;
        ARCHITECTURE.md)            guidance="Update architecture docs to reflect changes made" ;;
        SUBDOMAIN_ARCHITECTURE.md)  guidance="Update domain boundaries if new subdomains added" ;;
        ROADMAP.md)                 guidance="Mark completed items with [x], add new future TODOs" ;;
        PREPROD_CHECKLIST.md)       guidance="Check off completed pre-production items" ;;
        WORKFLOW_CATALOG.md)        guidance="Add Mermaid diagram if new workflow implemented" ;;
        *)                          guidance="Update as needed based on changes made" ;;
      esac
      doc_rows="${doc_rows}| \`${doc}\` | Update | ${guidance} |\n"
    fi
  done < <(jq -r '.known_docs[]' "$config_file" 2>/dev/null)

  if [[ "$found_any" == "true" ]]; then
    awk -v rows="$doc_rows" '
      /^## Documentation Updates Needed/ { in_section=1; print; next }
      in_section && /^\| Document \|/ { print; next }
      in_section && /^\|----------/ { print; printf "%s", rows; skip=1; next }
      in_section && skip && /^\|/ { next }
      in_section && skip && !/^\|/ { skip=0; in_section=0 }
      { print }
    ' "$output_file" > "${output_file}.tmp" && mv "${output_file}.tmp" "$output_file"
  fi
}

# --- Interactive doc selection ---

select_project_docs() {
  local project_dir="$1" config_file="$2"

  log "INFO" "Scanning for documentation files (.md only)..."
  echo ""

  local md_files=()
  while IFS= read -r file; do
    md_files+=("$file")
  done < <(find "$project_dir" \
    -name '*.md' \
    -not -path '*/.kh/*' \
    -not -path '*/.kanban/*' \
    -not -path '*/.git/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/vendor/*' \
    -not -path '*/__ARCHIVE__/*' \
    -not -path '*/docs/handoffs/*' \
    2>/dev/null | sort | while read -r f; do
      echo "${f#${project_dir}/}"
    done)

  if [[ ${#md_files[@]} -eq 0 ]]; then
    echo -e "${YELLOW}  No .md files found in project.${NC}"
    echo ""
    local temp_file; temp_file=$(mktemp)
    jq '.known_docs = []' "$config_file" > "$temp_file" && mv "$temp_file" "$config_file"
    return
  fi

  local i=1
  for file in "${md_files[@]}"; do
    echo "  ${i}) ${file}"
    i=$((i + 1))
  done
  echo ""
  echo -e "${YELLOW}Note:${NC} Currently only .md files are supported for automated doc updates."
  echo ""

  read -p "Select docs to update on feature changes (space-separated numbers, 'all', or 'none'): " selection

  local selected_docs=()
  if [[ "$selection" == "all" ]]; then
    selected_docs=("${md_files[@]}")
  elif [[ "$selection" == "none" || -z "$selection" ]]; then
    selected_docs=()
  else
    for num in $selection; do
      if [[ "$num" =~ ^[0-9]+$ ]] && [[ "$num" -ge 1 ]] && [[ "$num" -le ${#md_files[@]} ]]; then
        selected_docs+=("${md_files[$((num - 1))]}")
      else
        echo -e "${YELLOW}[WARN]${NC} Skipping invalid selection: $num"
      fi
    done
  fi

  local json_array="[]"
  for doc in "${selected_docs[@]}"; do
    json_array=$(echo "$json_array" | jq --arg d "$doc" '. + [$d]')
  done
  local temp_file; temp_file=$(mktemp)
  jq --argjson docs "$json_array" '.known_docs = $docs' "$config_file" > "$temp_file" && mv "$temp_file" "$config_file"

  echo ""
  log "INFO" "Selected ${#selected_docs[@]} docs for automated updates"
}

# --- Phase monitoring ---

parse_phase_markers() {
  local stream_file="$1"
  grep '"type"' "$stream_file" 2>/dev/null | grep '"assistant"' | \
    jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null | \
    grep -oE '\[PHASE: [A-Z_]+\]|\[TRIAGE: [A-Z_]+\]' || true
}

start_phase_monitor() {
  local id="$1" stream_file="$2"

  # Phase marker watcher
  (
    tail -f "$stream_file" 2>/dev/null | while IFS= read -r line; do
      echo "$line" | grep -q '"assistant"' || continue
      local text
      text=$(echo "$line" | jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null) || continue
      [[ -z "$text" ]] && continue

      if echo "$text" | grep -q '\[TRIAGE:'; then
        local triage_val
        triage_val=$(echo "$text" | grep -oE '\[TRIAGE: [A-Z_]+\]' | sed 's/\[TRIAGE: //;s/\]//' | tail -1)
        [[ -n "$triage_val" ]] && update_item "$id" "triage" "$triage_val"
      fi

      if echo "$text" | grep -q '\[PHASE: UPDATE_COMPLETE\]'; then
        update_item "$id" "phase" "done"
      elif echo "$text" | grep -q '\[PHASE: DEVELOPMENT_COMPLETE\]'; then
        update_item "$id" "phase" "update"
      elif echo "$text" | grep -q '\[PHASE: GROOMING_COMPLETE\]'; then
        update_item "$id" "phase" "development"
      fi
    done
  ) &
  PHASE_MONITOR_PID=$!

  # Stop sentinel watcher
  (
    while true; do
      sleep 2
      if [[ -f "${KH_DIR}/STOP" ]]; then
        rm -f "${KH_DIR}/STOP"
        echo -e "\033[1;33m[KH] Stop sentinel detected — killing active session...\033[0m" >&2
        kill -- -$$ 2>/dev/null || true
        exit 0
      fi
    done
  ) &
  STOP_MONITOR_PID=$!
}

stop_phase_monitor() {
  if [[ -n "${PHASE_MONITOR_PID:-}" ]]; then
    kill "$PHASE_MONITOR_PID" 2>/dev/null || true
    wait "$PHASE_MONITOR_PID" 2>/dev/null || true
    PHASE_MONITOR_PID=""
  fi
  if [[ -n "${STOP_MONITOR_PID:-}" ]]; then
    kill "$STOP_MONITOR_PID" 2>/dev/null || true
    wait "$STOP_MONITOR_PID" 2>/dev/null || true
    STOP_MONITOR_PID=""
  fi
}

# --- Token tracking ---

store_tokens() {
  local id="$1" result_json="$2"
  local input_tokens output_tokens cost_usd

  input_tokens=$(echo "$result_json" | jq -r '.usage.input_tokens // 0' 2>/dev/null)
  output_tokens=$(echo "$result_json" | jq -r '.usage.output_tokens // 0' 2>/dev/null)
  cost_usd=$(echo "$result_json" | jq -r '.cost_usd // .total_cost_usd // 0' 2>/dev/null)

  input_tokens="${input_tokens:-0}"; [[ "$input_tokens" =~ ^[0-9]+$ ]] || input_tokens=0
  output_tokens="${output_tokens:-0}"; [[ "$output_tokens" =~ ^[0-9]+$ ]] || output_tokens=0
  cost_usd="${cost_usd:-0}"; [[ "$cost_usd" =~ ^[0-9.]+$ ]] || cost_usd=0

  local temp_file timestamp
  temp_file=$(mktemp)
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  jq --arg id "$id" \
     --argjson inp "$input_tokens" --argjson out "$output_tokens" --arg cost "$cost_usd" \
     --arg ts "$timestamp" \
     '(.items[] | select(.id == $id)).tokens = {
        "input": $inp, "output": $out, "cost_usd": ($cost | tonumber)
      } | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  local total=$(( input_tokens + output_tokens ))
  local cost_fmt; cost_fmt=$(printf '%.2f' "$cost_usd")
  log "INFO" "Tokens $id: ${input_tokens} in + ${output_tokens} out = ${total} total (~\$${cost_fmt})"
  echo -e "  ${BLUE}Tokens:${NC} ${input_tokens} in + ${output_tokens} out = ${total} total (~${YELLOW}\$${cost_fmt}${NC})"
}

# --- Session management ---

save_session() {
  local id="$1" result_json="$2" prompt="${3:-}"
  local sessions_dir="${KH_DIR}/sessions"
  mkdir -p "$sessions_dir"
  echo "$result_json" | jq . > "${sessions_dir}/${id}_result.json" 2>/dev/null || \
    echo "$result_json" > "${sessions_dir}/${id}_result.json"
  [[ -n "$prompt" ]] && echo "$prompt" > "${sessions_dir}/${id}_prompt.txt"
  log "INFO" "Session saved: ${sessions_dir}/${id}_result.json"
}

# --- Failure display ---

show_failure_details() {
  local id="$1" output="$2"
  local session_file="${KH_DIR}/sessions/${id}_result.json"

  echo ""
  echo -e "${RED}───── failure details ─────${NC}"

  if [[ -f "$session_file" ]]; then
    local subtype num_turns cost
    subtype=$(jq -r '.subtype // empty' "$session_file")
    num_turns=$(jq -r '.num_turns // empty' "$session_file")
    cost=$(jq -r '.total_cost_usd // empty' "$session_file")

    if [[ "$subtype" == "error_max_turns" ]]; then
      local cost_fmt; cost_fmt=$(printf '%.2f' "$cost")
      echo -e "${YELLOW}Reason: Hit max-turns limit (${num_turns} turns, ~\$${cost_fmt})${NC}"
      echo -e "${YELLOW}Resume with: ${BLUE}kh resume ${id}${NC}"
    elif [[ -n "$subtype" ]]; then
      local cost_fmt; cost_fmt=$(printf '%.2f' "$cost")
      echo -e "${YELLOW}Reason: ${subtype} (${num_turns} turns, ~\$${cost_fmt})${NC}"
    fi
  fi

  if [[ -n "$output" ]]; then
    echo -e "${YELLOW}Output (last 20 lines):${NC}"
    echo "$output" | tail -20
  else
    echo -e "${YELLOW}(no output)${NC}"
  fi

  echo -e "${RED}──────────────────────────────${NC}"
}

# --- Completion detection (shared between process_item and resume) ---

finalize_item() {
  local id="$1" stream_file="$2" exit_code="$3" is_resumed="${4:-false}"
  local filename="${id}.md"
  local feature_name; feature_name=$(to_feature_name "$id")

  # Extract session_id from first system event
  local session_id
  session_id=$(grep -m1 '"type":"system"\|"type": "system"' "$stream_file" 2>/dev/null | jq -r '.session_id // empty' 2>/dev/null)
  [[ -n "$session_id" ]] && update_item "$id" "session_id" "$session_id"

  # Final pass: parse markers from completed stream
  local markers
  markers=$(parse_phase_markers "$stream_file")

  # Extract triage if not yet set
  local triage
  triage=$(jq -r --arg id "$id" '.items[] | select(.id == $id) | .triage // empty' "$STATE_FILE" 2>/dev/null)
  if [[ -z "$triage" || "$triage" == "null" ]]; then
    local found_triage
    found_triage=$(echo "$markers" | grep '\[TRIAGE:' | tail -1 | sed 's/.*\[TRIAGE: //;s/\].*//' || true)
    triage="${found_triage:-FEATURE}"
    update_item "$id" "triage" "$triage"
  fi

  # Phase reconciliation
  if echo "$markers" | grep -q "UPDATE_COMPLETE"; then
    update_item "$id" "phase" "done"
  elif echo "$markers" | grep -q "DEVELOPMENT_COMPLETE"; then
    update_item "$id" "phase" "update"
  elif echo "$markers" | grep -q "GROOMING_COMPLETE"; then
    update_item "$id" "phase" "development"
  fi

  # Extract result from stream
  local result
  result=$(grep '"type"' "$stream_file" 2>/dev/null | grep '"result"' | tail -1)
  echo "$result" | jq -e '.type == "result"' > /dev/null 2>&1 || result=""

  # Hard failure: bad exit code AND no result
  if [[ $exit_code -ne 0 && -z "$result" ]]; then
    log "ERROR" "Session failed for $id (exit code: $exit_code)"
    update_item "$id" "error" "Session failed (exit $exit_code)"
    mv "${DEV_DIR}/${filename}" "${DRAFT_DIR}/" 2>/dev/null || true
    update_item "$id" "state" "draft"
    update_item "$id" "phase" ""
    clear_global "active_session"
    warn "Returned to draft: ${id}"
    return
  fi

  local output subtype
  output=$(echo "$result" | jq -r '.result // empty')
  subtype=$(echo "$result" | jq -r '.subtype // empty')
  store_tokens "$id" "$result"
  save_session "$id" "$result" "$([[ "$is_resumed" == "true" ]] && echo "(resumed)" || echo "")"

  # Completion detection: 3 methods
  local delivery_file="" is_complete=false

  # Method 1: COMPLETE line in .result field
  if echo "$output" | grep -q "COMPLETE:"; then
    delivery_file=$(echo "$output" | grep "COMPLETE:" | tail -1 | sed 's/.*COMPLETE:[[:space:]]*//')
    is_complete=true
  fi

  # Method 2: COMPLETE in stream assistant text
  if [[ "$is_complete" == "false" ]]; then
    local stream_complete
    stream_complete=$(grep '"type"' "$stream_file" 2>/dev/null | grep '"assistant"' | \
      jq -r '.message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null | \
      grep "COMPLETE:" | tail -1 || true)
    if [[ -n "$stream_complete" ]]; then
      delivery_file=$(echo "$stream_complete" | sed 's/.*COMPLETE:[[:space:]]*//')
      is_complete=true
    fi
  fi

  # Method 3: UPDATE_COMPLETE marker → infer delivery filename
  if [[ "$is_complete" == "false" ]] && echo "$markers" | grep -q "UPDATE_COMPLETE"; then
    delivery_file="DELIVERY_${feature_name}.md"
    is_complete=true
    log "INFO" "Inferred completion from UPDATE_COMPLETE marker"
  fi

  if [[ "$is_complete" == "true" ]]; then
    log "INFO" "Complete: $id -> $delivery_file [${triage}]"
    update_item "$id" "delivery_handoff" "$delivery_file"
    update_item "$id" "completed_at" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    update_item "$id" "state" "complete"
    update_item "$id" "phase" "done"
    mv "${DEV_DIR}/${filename}" "${COMPLETE_DIR}/"
    clear_global "active_session"
    success "Complete: $id -> $delivery_file [${triage}]"
  else
    log "WARN" "Session did not complete cleanly for $id (subtype: $subtype)"
    update_item "$id" "error" "No COMPLETE marker in output (${subtype:-unknown})"
    show_failure_details "$id" "$output"
    mv "${DEV_DIR}/${filename}" "${DRAFT_DIR}/" 2>/dev/null || true
    update_item "$id" "state" "draft"
    update_item "$id" "phase" ""
    clear_global "active_session"
    warn "Returned to draft: ${id} (can retry with kh run)"
  fi
}

# --- Build doc update section for prompt ---

build_doc_section() {
  local config_file="$1" project_root="$2"
  local doc_section="" found_any=false

  while IFS= read -r doc; do
    if [[ -f "${project_root}/${doc}" ]]; then
      found_any=true
      local doc_basename guidance
      doc_basename=$(basename "$doc")
      case "$doc_basename" in
        PRIMER.md)                  guidance="Update current focus/state if project direction changed" ;;
        TECH_STACK.md)              guidance="Add new dependencies or tools introduced" ;;
        SETUP_GUIDE.md)             guidance="Update setup steps if new env vars or services added" ;;
        ARCHITECTURE_STATUS.md)     guidance="Add/update component descriptions and status" ;;
        ARCHITECTURE.md)            guidance="Update architecture docs to reflect changes made" ;;
        SUBDOMAIN_ARCHITECTURE.md)  guidance="Update domain boundaries if new subdomains added" ;;
        ROADMAP.md)                 guidance="Mark completed items with [x], add new future TODOs" ;;
        PREPROD_CHECKLIST.md)       guidance="Check off completed pre-production items" ;;
        WORKFLOW_CATALOG.md)        guidance="Add Mermaid diagram if new workflow implemented" ;;
        *)                          guidance="Update as needed based on changes made" ;;
      esac
      doc_section="${doc_section}
- **${doc_basename}** (\`${doc}\`): ${guidance}"
    fi
  done < <(jq -r '.known_docs[]' "$config_file" 2>/dev/null)

  if [[ "$found_any" == "true" ]]; then
    echo "Update these project docs based on the changes you made:
${doc_section}
- Update the DELIVERY_HANDOFF status to: UPDATES_COMPLETE"
  else
    echo "No project docs configured for updates. Just mark the DELIVERY_HANDOFF status as UPDATES_COMPLETE."
  fi
}

# ═══════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════

cmd_init() {
  local project_dir="$PWD"
  local kh_dir="${project_dir}/.kh"

  echo -e "${BLUE}Initializing ThousandHand in: ${project_dir}${NC}"

  mkdir -p "${kh_dir}/draft" "${kh_dir}/developing" "${kh_dir}/complete" "${kh_dir}/sessions"

  if [[ ! -f "${kh_dir}/config.json" ]]; then
    local project_name
    project_name=$(basename "$project_dir")
    jq --arg name "$project_name" --arg root "." \
       '.project_name = $name | .project_root = $root' \
       "${KH_DEFAULTS}/config.json" > "${kh_dir}/config.json"
    log "INFO" "Created config.json"
  fi

  [[ -f "${kh_dir}/state.json" ]] || cp "${KH_DEFAULTS}/state.json" "${kh_dir}/state.json"

  mkdir -p "${project_dir}/docs/handoffs"

  select_project_docs "$project_dir" "${kh_dir}/config.json"

  generate_grooming_standards "$kh_dir" "$project_dir"
  log "INFO" "Generated .kh/templates/GROOMING_STANDARDS.md"

  generate_local_delivery_template "$kh_dir" "$project_dir"
  log "INFO" "Generated .kh/templates/DELIVERY_HANDOFF_TEMPLATE.md"

  LOG_FILE="${kh_dir}/kh.log"
  log "INFO" "ThousandHand initialized in ${project_dir}"
}

cmd_add() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local draft_file="${DRAFT_DIR}/${safe_name}.md"

  log "INFO" "Adding draft: $name"

  local content
  [[ -t 0 ]] && echo -e "${YELLOW}Enter draft content (Ctrl+D when done):${NC}"
  content=$(cat)

  if [[ -z "$content" ]]; then
    error "No content provided."
    echo "  kh add \"name\" <<< 'one-liner draft'"
    echo "  kh add \"name\" < draft.md"
    echo "  kh add \"name\" << 'EOF'"
    echo "  Multi-line content here"
    echo "  EOF"
    exit 1
  fi

  printf '%s\n' "$content" > "$draft_file"

  local timestamp next_priority temp_file
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  next_priority=$(jq '.items | length' "$STATE_FILE")
  temp_file=$(mktemp)

  jq --arg id "$safe_name" --arg file "${safe_name}.md" --arg ts "$timestamp" --argjson pri "$next_priority" \
     '.items += [{
       "id": $id, "draft_file": $file, "state": "draft", "phase": null,
       "session_id": null, "delivery_handoff": null, "triage": null,
       "priority": $pri, "tokens": {}, "started_at": $ts,
       "completed_at": null, "error": null
     }] | .last_updated = $ts' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  log "INFO" "Draft added: $draft_file"
  success "Draft added: $safe_name"
}

cmd_status() {
  resolve_paths
  echo ""
  header
  echo -e "${BLUE}                     THOUSANDHAND STATUS                     ${NC}"
  header

  if [[ -f "$CONFIG_FILE" ]]; then
    echo -e "  Project: ${YELLOW}$(jq -r '.project_name' "$CONFIG_FILE")${NC}"
  fi
  echo ""

  local draft_count complete_count grooming_count developing_count updating_count
  draft_count=$(ls -1 "$DRAFT_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ' || echo 0)
  complete_count=$(ls -1 "$COMPLETE_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ' || echo 0)

  if [[ -f "$STATE_FILE" ]]; then
    grooming_count=$(jq '[.items[] | select(.state == "developing" and .phase == "grooming")] | length' "$STATE_FILE")
    developing_count=$(jq '[.items[] | select(.state == "developing" and .phase == "development")] | length' "$STATE_FILE")
    updating_count=$(jq '[.items[] | select(.state == "developing" and .phase == "update")] | length' "$STATE_FILE")
  else
    grooming_count=0; developing_count=0; updating_count=0
  fi

  # Display each queue
  for label_emoji_var_count in \
    "DRAFT:📋:draft:${draft_count}" \
    "GROOMING:🔄:grooming:${grooming_count}" \
    "DEVELOPING:🔨:developing:${developing_count}" \
    "UPDATING:📝:updating:${updating_count}" \
    "COMPLETE:✅:complete:${complete_count}"; do
    IFS=: read -r label emoji qtype count <<< "$label_emoji_var_count"
    echo -e "${emoji} ${YELLOW}${label}${NC} ($count items):"
    if [[ "$count" -gt 0 ]]; then
      case "$qtype" in
        draft)      ls -1 "$DRAFT_DIR"/*.md 2>/dev/null | xargs -I {} basename {} | sed 's/^/   /' ;;
        complete)   ls -1 "$COMPLETE_DIR"/*.md 2>/dev/null | xargs -I {} basename {} | sed 's/^/   /' ;;
        grooming)   jq -r '.items[] | select(.state == "developing" and .phase == "grooming") | "   \(.id).md"' "$STATE_FILE" ;;
        developing) jq -r '.items[] | select(.state == "developing" and .phase == "development") | "   \(.id).md"' "$STATE_FILE" ;;
        updating)   jq -r '.items[] | select(.state == "developing" and .phase == "update") | "   \(.id).md"' "$STATE_FILE" ;;
      esac
    else
      echo "   (empty)"
    fi
    echo ""
  done

  header
  echo "Active Session:"
  if [[ -f "$STATE_FILE" ]]; then
    echo "  $(jq -r '.active_session // "none"' "$STATE_FILE")"
  fi
  echo ""
  echo "Token Usage:"
  if [[ -f "$STATE_FILE" ]]; then
    local total_in total_out total_cost
    total_in=$(jq '[.items[].tokens // {} | .input // 0] | add // 0' "$STATE_FILE" 2>/dev/null || echo 0)
    total_out=$(jq '[.items[].tokens // {} | .output // 0] | add // 0' "$STATE_FILE" 2>/dev/null || echo 0)
    total_cost=$(jq '[.items[].tokens // {} | .cost_usd // 0] | add // 0' "$STATE_FILE" 2>/dev/null || echo 0)
    local cost_fmt; cost_fmt=$(printf '%.2f' "$total_cost")
    echo -e "  ${total_in} in + ${total_out} out = $(( total_in + total_out )) total (~${YELLOW}\$${cost_fmt}${NC})"
  fi
  header
}

cmd_process_item() {
  load_config

  # Check no active session
  local current_active
  current_active=$(jq -r '.active_session // empty' "$STATE_FILE")
  if [[ -n "$current_active" && "$current_active" != "null" ]]; then
    log "INFO" "Session already active: $current_active"
    return
  fi

  # Find next draft by priority
  local next_id
  next_id=$(jq -r '[.items[] | select(.state == "draft")] | sort_by(.priority // 0, .started_at) | .[0].id // empty' "$STATE_FILE")
  [[ -z "$next_id" ]] && { log "INFO" "No draft items to process"; return; }

  local id="$next_id"
  local filename="${id}.md"
  local feature_name; feature_name=$(to_feature_name "$id")

  log "INFO" "Processing item: $id"

  # Move draft → developing
  mv "${DRAFT_DIR}/${filename}" "${DEV_DIR}/"
  update_item "$id" "state" "developing"
  update_item "$id" "phase" "grooming"
  update_global "active_session" "$id"

  local draft_content
  draft_content=$(cat "${DEV_DIR}/${filename}")

  # Resolve templates
  local grooming_standards="${KH_DIR}/templates/GROOMING_STANDARDS.md"
  [[ -f "$grooming_standards" ]] || grooming_standards="${KH_TEMPLATES}/MASTER_GROOMING_STANDARDS.md"
  local del_template="${KH_DIR}/templates/DELIVERY_HANDOFF_TEMPLATE.md"
  [[ -f "$del_template" ]] || del_template="${KH_TEMPLATES}/MASTER_DELIVERY_HANDOFF_TEMPLATE.md"

  local doc_section
  doc_section=$(build_doc_section "$CONFIG_FILE" "$PROJECT_ROOT")

  # Consolidated 3-phase prompt
  local prompt="> BEST EFFORTS / AGGRESSIVE EXECUTION. Move fast, assume and document.

You are processing a task through 3 phases in a SINGLE SESSION:
GROOMING -> DEVELOPMENT -> UPDATE.
Do NOT create a separate grooming handoff file — analyze inline.

INPUT DRAFT:
${draft_content}

REFERENCE FILES (read at start):
- Grooming standards: ${grooming_standards}
- Delivery handoff template: ${del_template}
- Project ROADMAP: ${DOCS_PATH}/ROADMAP.md
- Project TECH_STACK: ${DOCS_PATH}/TECH_STACK.md

## PHASE 1: GROOMING
1. Read grooming standards + project docs
2. TRIAGE: classify as FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION
3. Emit: [TRIAGE: <classification>]
4. Analyze: objective, scope, success criteria, architecture (WHAT not HOW)
5. Validate scope (>5 files -> note for consideration)
6. Emit: [PHASE: GROOMING_COMPLETE]

## PHASE 2: DEVELOPMENT
1. Read codebase, determine HOW
2. Implement based on grooming analysis
3. Write tests (per triage level)
4. Create DELIVERY_HANDOFF -> ${HANDOFFS_PATH}/DELIVERY_${feature_name}.md
5. Emit: [PHASE: DEVELOPMENT_COMPLETE]

## PHASE 3: UPDATE
${doc_section}
(If DOCUMENTATION triage: lightweight — just mark DELIVERY_HANDOFF as UPDATES_COMPLETE)
Emit: [PHASE: UPDATE_COMPLETE]

COMPLETE: DELIVERY_${feature_name}.md"

  check_stop_sentinel

  log "INFO" "Launching consolidated session for: $id"

  local stream_file="${KH_DIR}/sessions/${id}_stream.jsonl"
  echo "$stream_file" > "${KH_DIR}/active_stream"

  touch "$stream_file"
  start_phase_monitor "$id" "$stream_file"

  local exit_code=0
  ( cd "$PROJECT_ROOT" && claude -p "$prompt" \
    --model "$MODEL" \
    --dangerously-skip-permissions \
    --verbose --output-format stream-json \
    --max-turns 100 \
  ) > "$stream_file" 2>&1 || exit_code=$?

  stop_phase_monitor
  rm -f "${KH_DIR}/active_stream"

  finalize_item "$id" "$stream_file" "$exit_code" "false"
}

cmd_run() {
  load_config
  log "INFO" "Running..."
  header
  echo -e "${BLUE}                     THOUSANDHAND RUN                         ${NC}"
  header
  echo ""

  local consecutive_failures=0
  local max_failures=3
  local last_failed_id=""

  while true; do
    local has_drafts
    has_drafts=$(ls -1 "$DRAFT_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [[ "$has_drafts" -eq 0 ]] && break
    check_stop_sentinel

    # Track which item will be processed next
    local next_id
    next_id=$(jq -r '[.items[] | select(.state == "draft")] | sort_by(.priority // 0, .started_at) | .[0].id // empty' "$STATE_FILE")

    cmd_process_item

    # Check if the same item failed again (it returns to draft on failure)
    local post_state
    post_state=$(jq -r --arg id "$next_id" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE" 2>/dev/null)
    if [[ "$post_state" == "draft" && "$next_id" == "$last_failed_id" ]]; then
      consecutive_failures=$((consecutive_failures + 1))
      if [[ $consecutive_failures -ge $max_failures ]]; then
        error "Item '${next_id}' failed ${max_failures} times consecutively. Halting."
        error "Check config and logs, then retry with: kh run"
        return 1
      fi
    else
      consecutive_failures=0
    fi
    last_failed_id="$next_id"
  done

  log "INFO" "Run complete"
  success "Run complete!"
}

cmd_view() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local filename="${safe_name}.md"

  for dir in "$DRAFT_DIR" "$DEV_DIR" "$COMPLETE_DIR"; do
    if [[ -f "${dir}/${filename}" ]]; then
      local queue_name; queue_name=$(basename "$dir")
      header
      echo -e "  ${YELLOW}${safe_name}${NC}  (queue: ${queue_name})"
      echo -e "  ${GREEN}${dir}/${filename}${NC}"
      header
      echo ""
      cat "${dir}/${filename}"
      echo ""

      if [[ -f "$STATE_FILE" ]]; then
        local item_json
        item_json=$(jq --arg id "$safe_name" '.items[] | select(.id == $id)' "$STATE_FILE" 2>/dev/null)
        if [[ -n "$item_json" ]]; then
          echo -e "${BLUE}───── state ─────${NC}"
          echo "$item_json" | jq .
        fi

        local delivery_handoff
        delivery_handoff=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .delivery_handoff // empty' "$STATE_FILE" 2>/dev/null)
        if [[ -n "$delivery_handoff" && -f "${HANDOFFS_PATH}/${delivery_handoff}" ]]; then
          echo ""
          echo -e "${BLUE}───── delivery handoff ─────${NC}"
          echo -e "  ${GREEN}${HANDOFFS_PATH}/${delivery_handoff}${NC}"
        fi

        local has_tokens
        has_tokens=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .tokens // {} | length' "$STATE_FILE" 2>/dev/null)
        if [[ "$has_tokens" -gt 0 ]]; then
          echo ""
          echo -e "${BLUE}───── tokens ─────${NC}"
          local item_in item_out item_cost item_cost_fmt
          item_in=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .tokens.input // 0' "$STATE_FILE")
          item_out=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .tokens.output // 0' "$STATE_FILE")
          item_cost=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .tokens.cost_usd // 0' "$STATE_FILE")
          item_cost_fmt=$(printf '%.2f' "$item_cost")
          echo -e "  ${item_in} in + ${item_out} out = $(( item_in + item_out )) total (~${YELLOW}\$${item_cost_fmt}${NC})"
        fi
      fi
      return 0
    fi
  done

  # Check handoff docs as fallback
  local feature_name; feature_name=$(to_feature_name "$safe_name")
  local handoff_file="${HANDOFFS_PATH}/DELIVERY_${feature_name}.md"
  if [[ -f "$handoff_file" ]]; then
    header
    echo -e "  ${YELLOW}${safe_name}${NC}  (handoff: DELIVERY_${feature_name}.md)"
    header
    echo ""
    cat "$handoff_file"
    return 0
  fi

  error "No file found for '${name}'"
  echo "Searched all queues and handoffs for: ${filename}"
  exit 1
}

cmd_demote() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local filename="${safe_name}.md"

  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE")
  [[ -z "$current_state" ]] && { error "Item '${name}' not found in state.json"; exit 1; }
  [[ "$current_state" == "draft" ]] && { echo -e "${YELLOW}Already in draft.${NC}"; return; }

  local source_dir=""
  case "$current_state" in
    developing) source_dir="$DEV_DIR" ;;
    complete)   source_dir="$COMPLETE_DIR" ;;
  esac
  [[ -n "$source_dir" ]] && mv "${source_dir}/${filename}" "${DRAFT_DIR}/" 2>/dev/null || true

  # Delete delivery handoff if exists
  local delivery_handoff
  delivery_handoff=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .delivery_handoff // empty' "$STATE_FILE")
  if [[ -n "$delivery_handoff" && -f "${HANDOFFS_PATH}/${delivery_handoff}" ]]; then
    rm "${HANDOFFS_PATH}/${delivery_handoff}"
    echo -e "${YELLOW}Deleted:${NC} ${HANDOFFS_PATH}/${delivery_handoff}"
  fi

  # Clear active session if needed
  local active; active=$(jq -r '.active_session // empty' "$STATE_FILE")
  [[ "$active" == "$safe_name" ]] && clear_global "active_session"

  # Reset fields
  update_item "$safe_name" "state" "draft"
  update_item "$safe_name" "phase" ""
  update_item "$safe_name" "delivery_handoff" ""
  update_item "$safe_name" "triage" ""
  update_item "$safe_name" "error" ""
  # Clear session_id (needs null, not empty string)
  local temp_file timestamp
  temp_file=$(mktemp); timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "$safe_name" --arg ts "$timestamp" \
     '(.items[] | select(.id == $id)).session_id = null | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  log "INFO" "Demoted $safe_name from $current_state -> draft"
  success "Demoted: ${safe_name} (${current_state} -> draft)"
}

cmd_promote() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local filename="${safe_name}.md"

  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE")
  [[ -z "$current_state" ]] && { error "Item '${name}' not found in state.json"; exit 1; }
  [[ "$current_state" == "complete" ]] && { echo -e "${YELLOW}Already complete.${NC}"; return; }

  local source_dir=""
  case "$current_state" in
    draft)      source_dir="$DRAFT_DIR" ;;
    developing) source_dir="$DEV_DIR" ;;
  esac

  # Auto-detect delivery handoff
  local feature_upper; feature_upper=$(to_feature_name "$safe_name")
  local found_handoff=""
  for f in "${HANDOFFS_PATH}"/DELIVERY_*"${feature_upper}"*.md "${HANDOFFS_PATH}"/DELIVERY_*"$(echo "$safe_name" | tr '-' '_')"*.md; do
    [[ -f "$f" ]] && found_handoff=$(basename "$f") && break
  done

  if [[ -n "$found_handoff" ]]; then
    echo -e "Found delivery handoff: ${GREEN}${found_handoff}${NC}"
    read -p "Use this file? [Y/n/path/skip] " choice
    case "$choice" in
      n|N) read -p "Enter delivery handoff filename: " found_handoff ;;
      skip|s) found_handoff="" ;;
      "") ;; # accept default
      *) found_handoff="$choice" ;;
    esac
  else
    echo "No delivery handoff auto-detected."
    read -p "Enter delivery handoff filename (or 'skip' for none): " found_handoff
    [[ "$found_handoff" == "skip" ]] && found_handoff=""
  fi

  [[ -n "$found_handoff" ]] && update_item "$safe_name" "delivery_handoff" "$found_handoff"

  update_item "$safe_name" "completed_at" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  update_item "$safe_name" "state" "complete"
  update_item "$safe_name" "phase" "done"
  mv "${source_dir}/${filename}" "${COMPLETE_DIR}/" 2>/dev/null || true

  local active; active=$(jq -r '.active_session // empty' "$STATE_FILE")
  [[ "$active" == "$safe_name" ]] && clear_global "active_session"

  log "INFO" "Promoted $safe_name from $current_state -> complete"
  success "Promoted: ${safe_name} -> complete"
}

cmd_resume() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local filename="${safe_name}.md"

  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE")
  [[ -z "$current_state" ]] && { error "Item '${name}' not found in state.json"; exit 1; }
  [[ "$current_state" != "draft" ]] && { echo -e "${YELLOW}Can only resume items in draft state (current: ${current_state}).${NC}"; return; }

  local session_id
  session_id=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .session_id // empty' "$STATE_FILE" 2>/dev/null)
  [[ -z "$session_id" || "$session_id" == "null" ]] && { error "No session_id found for '${safe_name}'. Nothing to resume."; return; }

  log "INFO" "Resuming session for ${safe_name} (session: ${session_id})"
  echo -e "${BLUE}Resuming session:${NC} ${session_id}"

  # Determine phase from existing markers
  local stream_file="${KH_DIR}/sessions/${safe_name}_stream.jsonl"
  local resume_phase="grooming"
  if [[ -f "$stream_file" ]]; then
    local markers; markers=$(parse_phase_markers "$stream_file")
    if echo "$markers" | grep -q "DEVELOPMENT_COMPLETE"; then
      resume_phase="update"
    elif echo "$markers" | grep -q "GROOMING_COMPLETE"; then
      resume_phase="development"
    fi
  fi

  log "INFO" "Resuming at phase: ${resume_phase}"
  echo -e "  Phase: ${MAGENTA}${resume_phase}${NC}"

  mv "${DRAFT_DIR}/${filename}" "${DEV_DIR}/" 2>/dev/null || true
  update_item "$safe_name" "state" "developing"
  update_item "$safe_name" "phase" "$resume_phase"
  update_global "active_session" "$safe_name"

  local feature_name; feature_name=$(to_feature_name "$safe_name")
  local resume_prompt=""
  case "$resume_phase" in
    grooming)
      resume_prompt="Continue where you left off. You are in the GROOMING phase.
When grooming is done, emit [PHASE: GROOMING_COMPLETE] and proceed to DEVELOPMENT.
After development, emit [PHASE: DEVELOPMENT_COMPLETE] and proceed to UPDATE.
After update, emit [PHASE: UPDATE_COMPLETE].
When fully complete, output EXACTLY: COMPLETE: DELIVERY_${feature_name}.md" ;;
    development)
      resume_prompt="Continue where you left off. You completed GROOMING. You are in the DEVELOPMENT phase.
After development, emit [PHASE: DEVELOPMENT_COMPLETE] and proceed to UPDATE.
After update, emit [PHASE: UPDATE_COMPLETE].
When fully complete, output EXACTLY: COMPLETE: DELIVERY_${feature_name}.md" ;;
    update)
      resume_prompt="Continue where you left off. You completed GROOMING and DEVELOPMENT. You are in the UPDATE phase.
Update project docs as needed, then emit [PHASE: UPDATE_COMPLETE].
When fully complete, output EXACTLY: COMPLETE: DELIVERY_${feature_name}.md" ;;
  esac

  echo "$stream_file" > "${KH_DIR}/active_stream"
  start_phase_monitor "$safe_name" "$stream_file"

  local exit_code=0
  ( cd "$PROJECT_ROOT" && claude --resume "$session_id" \
    -p "$resume_prompt" \
    --dangerously-skip-permissions \
    --verbose --output-format stream-json \
  ) >> "$stream_file" 2>&1 || exit_code=$?

  stop_phase_monitor
  rm -f "${KH_DIR}/active_stream"

  finalize_item "$safe_name" "$stream_file" "$exit_code" "true"
}

cmd_remove() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local filename="${safe_name}.md"

  load_config

  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE")
  [[ -z "$current_state" ]] && { error "Item '${name}' not found in state.json"; exit 1; }

  local queue_dir=""
  case "$current_state" in
    draft)      queue_dir="$DRAFT_DIR" ;;
    developing) queue_dir="$DEV_DIR" ;;
    complete)   queue_dir="$COMPLETE_DIR" ;;
  esac

  [[ -n "$queue_dir" && -f "${queue_dir}/${filename}" ]] && {
    rm "${queue_dir}/${filename}"
    echo -e "${YELLOW}Deleted:${NC} ${queue_dir}/${filename}"
  }

  local delivery_handoff
  delivery_handoff=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .delivery_handoff // empty' "$STATE_FILE")
  [[ -n "$delivery_handoff" && -f "${HANDOFFS_PATH}/${delivery_handoff}" ]] && {
    rm "${HANDOFFS_PATH}/${delivery_handoff}"
    echo -e "${YELLOW}Deleted:${NC} ${HANDOFFS_PATH}/${delivery_handoff}"
  }

  local active; active=$(jq -r '.active_session // empty' "$STATE_FILE")
  [[ "$active" == "$safe_name" ]] && clear_global "active_session"

  local temp_file timestamp
  temp_file=$(mktemp); timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "$safe_name" --arg ts "$timestamp" \
     '.items = [.items[] | select(.id != $id)] | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  log "INFO" "Removed item: $safe_name (was $current_state)"
  success "Removed: ${safe_name} (was ${current_state})"
}

# Shared jq filter for stream display (used by both live and replay modes)
STREAM_JQ_FILTER='
  if .type == "system" then
    "[\u001b[34msession\u001b[0m] \(.session_id // "starting...")"
  elif .type == "assistant" then
    [.message.content[]? |
      if .type == "tool_use" then
        "[\u001b[32mtool\u001b[0m] \(.name): \(
          if .name == "Read" or .name == "Write" or .name == "Edit" then (.input.file_path // "")
          elif .name == "Bash" then (.input.command // "" | tostring | .[0:100])
          elif .name == "Glob" then (.input.pattern // "")
          elif .name == "Grep" then "\(.input.pattern // "") in \(.input.path // ".")"
          else (.input | keys | join(", "))
          end
        )"
      elif .type == "text" then
        (.text // "" | capture("(?<m>\\[PHASE: [A-Z_]+\\])") | "\u001b[35m\(.m)\u001b[0m") // empty,
        (.text // "" | capture("(?<m>\\[TRIAGE: [A-Z_]+\\])") | "\u001b[36m\(.m)\u001b[0m") // empty
      else empty
      end
    ] | join("\n") | select(. != "")
  elif .type == "result" then
    "[\u001b[33mdone\u001b[0m] \(.subtype // "unknown") | \(.num_turns // 0) turns | ~$\(.total_cost_usd // 0 | . * 100 | round / 100)"
  else empty
  end
'

cmd_logs() {
  resolve_paths
  local stream_file="" is_live="false"

  if [[ -f "${KH_DIR}/active_stream" ]]; then
    stream_file=$(cat "${KH_DIR}/active_stream")
    [[ -f "$stream_file" ]] && is_live="true"
  fi
  [[ -z "$stream_file" || ! -f "$stream_file" ]] && \
    stream_file=$(ls -t "${KH_DIR}/sessions/"*_stream.jsonl 2>/dev/null | head -1)
  [[ -z "$stream_file" || ! -f "$stream_file" ]] && { echo -e "${YELLOW}No session stream found.${NC}"; return; }

  local basename_file; basename_file=$(basename "$stream_file" _stream.jsonl)

  if [[ "$is_live" == "true" ]]; then
    echo -e "${GREEN}● Live session:${NC} ${basename_file}"
    echo -e "${YELLOW}  Press Ctrl+C to stop watching${NC}"
    echo ""
    tail -f -n +1 "$stream_file" | jq -r --unbuffered "$STREAM_JQ_FILTER" 2>/dev/null
  else
    echo -e "${BLUE}● Last session:${NC} ${basename_file}"
    echo ""
    jq -r "$STREAM_JQ_FILTER" "$stream_file" 2>/dev/null
  fi
}

cmd_prioritize() {
  local name="$1" new_priority="$2"
  local safe_name; safe_name=$(to_safe_name "$name")

  [[ "$new_priority" =~ ^[0-9]+$ ]] || { error "Priority must be a non-negative integer. Got: '${new_priority}'"; exit 1; }

  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE")
  [[ -z "$current_state" ]] && { error "Item '${name}' not found in state.json"; exit 1; }

  local temp_file timestamp
  temp_file=$(mktemp); timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg id "$safe_name" --argjson pri "$new_priority" --arg ts "$timestamp" \
     '(.items[] | select(.id == $id)).priority = $pri | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  log "INFO" "Reprioritized $safe_name -> priority $new_priority"
  success "${safe_name} priority set to ${new_priority} (lower = first)"
  echo ""
  echo -e "${BLUE}Current priority order:${NC}"
  jq -r '.items[] | select(.state == "draft") | "  \(.priority // 0)\t\(.id)"' "$STATE_FILE" | sort -n
}

cmd_watch() {
  load_config
  log "INFO" "Starting watch mode (poll interval: ${POLL_INTERVAL}s)"
  echo -e "${BLUE}Starting watch mode... Ctrl+C or 'kh stop' to halt${NC}"
  while true; do
    check_stop_sentinel
    cmd_run
    echo ""
    check_stop_sentinel
    echo -e "${YELLOW}Sleeping ${POLL_INTERVAL}s before next pass...${NC}"
    sleep "$POLL_INTERVAL"
  done
}

cmd_stop() {
  resolve_paths
  touch "${KH_DIR}/STOP"
  log "INFO" "Stop sentinel written"
  echo -e "${YELLOW}Stop sentinel written.${NC} KH will halt after the current Claude call finishes."
  echo "If stuck: ${BLUE}kill \$(pgrep -f 'kh.sh')${NC}"
}

# ═══════════════════════════════════════════════════════════
# MAIN DISPATCH
# ═══════════════════════════════════════════════════════════

main() {
  case "${1:-}" in
    init)
      cmd_init ;;
    add)
      [[ -z "${2:-}" ]] && { echo "Usage: kh add \"item-name\" <<< 'draft content'"; exit 1; }
      load_config; cmd_add "$2" ;;
    view)
      [[ -z "${2:-}" ]] && { echo "Usage: kh view \"item-name\""; exit 1; }
      load_config; cmd_view "$2" ;;
    remove)
      [[ -z "${2:-}" ]] && { echo "Usage: kh remove \"item-name\""; exit 1; }
      cmd_remove "$2" ;;
    demote)
      [[ -z "${2:-}" ]] && { echo "Usage: kh demote \"item-name\""; exit 1; }
      load_config; cmd_demote "$2" ;;
    promote)
      [[ -z "${2:-}" ]] && { echo "Usage: kh promote \"item-name\""; exit 1; }
      load_config; cmd_promote "$2" ;;
    resume)
      [[ -z "${2:-}" ]] && { echo "Usage: kh resume \"item-name\""; exit 1; }
      load_config; cmd_resume "$2" ;;
    prioritize)
      [[ -z "${2:-}" || -z "${3:-}" ]] && { echo "Usage: kh prioritize \"item-name\" <priority>"; exit 1; }
      load_config; cmd_prioritize "$2" "$3" ;;
    status)
      cmd_status ;;
    run)
      cmd_run ;;
    watch)
      cmd_watch ;;
    logs)
      cmd_logs ;;
    stop)
      cmd_stop ;;
    help|--help|-h)
      echo ""
      echo -e "${BLUE}ThousandHand (KH)${NC} - Claude Workflow Orchestration"
      echo ""
      echo "Usage: kh <command>"
      echo ""
      echo -e "${YELLOW}Setup:${NC}"
      echo "  init                    Initialize .kh structure"
      echo "  add \"name\"              Add draft from stdin (pipe or heredoc)"
      echo "  status                  Show queue status + active phase"
      echo "  view \"name\"             View task file + metadata"
      echo "  prioritize \"name\" <n>   Set priority (lower = processed first)"
      echo ""
      echo -e "${YELLOW}Processing:${NC}"
      echo "  run                     Process all drafts (single session per item)"
      echo "  logs                    Live-tail active session (or show last)"
      echo "  watch                   Continuous monitoring mode"
      echo "  stop                    Graceful halt (from another terminal)"
      echo ""
      echo -e "${YELLOW}Management:${NC}"
      echo "  demote \"name\"           Move back to draft (redo)"
      echo "  promote \"name\"          Manually advance to complete"
      echo "  resume \"name\"           Resume a failed session from checkpoint"
      echo "  remove \"name\"           Permanently delete item + files"
      echo ""
      ;;
    *)
      echo ""
      echo -e "${BLUE}ThousandHand (KH)${NC} - Claude Workflow Orchestration"
      echo ""
      echo "Usage: kh <command>"
      echo ""
      echo "  init | add | status | view | prioritize"
      echo "  run | logs | watch | stop"
      echo "  demote | promote | resume | remove"
      echo ""
      echo "Run 'kh help' for details."
      echo ""
      ;;
  esac
}

main "$@"
