#!/bin/bash
#
# ThousandHand (KH) - Filesystem-based Claude workflow orchestration
#
# Usage:
#   kh raw "name"              Add raw brain dump from stdin
#   kh raw list                List all raw inputs + status
#   kh raw show "name"         Show raw input + breakdown report
#   kh breakdown "name"        AI triage: split raw into discrete drafts
#   kh breakdown "name" --dry-run  Preview breakdown without creating files
#
#   kh init                    Initialize .kh structure in current directory
#   kh add "name"              Add discrete draft from stdin (skip pre-flow)
#   kh status                  Show current queue status + active phase
#   kh view "name"             View a task file and its metadata
#   kh prioritize "name" <n>   Set task priority (lower = first)
#
#   kh run                     Process all drafts (single Opus session per item)
#   kh logs                    Live-tail active Claude session
#   kh watch                   Continuous monitoring mode
#   kh stop                    Stop a running watch/run (from another terminal)
#
#   kh close [modifier]        Closing ceremony — comprehensive review + UAT prep
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
KH_PROTOCOLS="${KH_HOME}/protocols"
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

# --- Scope Gating ---
# Checks if any JM in JOURNEY_MAPPINGS.md has IMPLEMENTED or IN PROGRESS status.
# Used by cmd_breakdown() to redirect JM_NEW items to deferred_scope.

has_active_jm_scope() {
  local jm_context="$1"
  if echo "$jm_context" | grep -qiE 'IMPLEMENTED|IN PROGRESS'; then
    return 0  # true — active scope exists
  fi
  return 1  # false — no active scope
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
  RAW_DIR="${KH_DIR}/raw"
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
  local is_reinit=false

  [[ -d "$kh_dir" ]] && is_reinit=true

  echo -e "${BLUE}Initializing ThousandHand in: ${project_dir}${NC}"
  [[ "$is_reinit" == "true" ]] && echo -e "${YELLOW}Re-initializing — config and state preserved, templates refreshed.${NC}"

  mkdir -p "${kh_dir}/draft" "${kh_dir}/developing" "${kh_dir}/complete" "${kh_dir}/sessions" "${kh_dir}/raw"

  if [[ ! -f "${kh_dir}/config.json" ]]; then
    local project_name
    project_name=$(basename "$project_dir")
    jq --arg name "$project_name" --arg root "." \
       '.project_name = $name | .project_root = $root' \
       "${KH_DEFAULTS}/config.json" > "${kh_dir}/config.json"
    log "INFO" "Created config.json"
  else
    # Ensure new config fields exist (migration for existing projects)
    local temp_file; temp_file=$(mktemp)
    jq '. + {execution_context: (.execution_context // "local"), template_version: (.template_version // "0.0.0")}' \
       "${kh_dir}/config.json" > "$temp_file" && mv "$temp_file" "${kh_dir}/config.json"
  fi

  [[ -f "${kh_dir}/state.json" ]] || cp "${KH_DEFAULTS}/state.json" "${kh_dir}/state.json"

  mkdir -p "${project_dir}/docs/handoffs"

  # Execution context selection (only on first init or if explicitly re-selecting)
  local current_context
  current_context=$(jq -r '.execution_context // "local"' "${kh_dir}/config.json")
  if [[ "$is_reinit" == "false" ]] || [[ "$current_context" == "local" && "$is_reinit" == "true" ]]; then
    echo ""
    echo -e "${YELLOW}Execution Context:${NC}"
    echo "  1) local       — SQLite, mocks, localhost (early development)"
    echo "  2) mixed       — Some cloud services live, some local (incremental integration)"
    echo "  3) production  — All services production (post-go-live)"
    echo ""
    read -p "Select execution context [1/2/3] (current: ${current_context}): " ctx_choice
    case "$ctx_choice" in
      2|mixed)      current_context="mixed" ;;
      3|production) current_context="production" ;;
      1|local|"")   current_context="local" ;;
      *)            current_context="local" ;;
    esac
    local temp_file; temp_file=$(mktemp)
    jq --arg ctx "$current_context" '.execution_context = $ctx' \
       "${kh_dir}/config.json" > "$temp_file" && mv "$temp_file" "${kh_dir}/config.json"
    log "INFO" "Execution context set to: ${current_context}"
  fi
  echo -e "  Context: ${CYAN}${current_context}${NC}"

  # Doc selection (only on first init)
  if [[ "$is_reinit" == "false" ]]; then
    select_project_docs "$project_dir" "${kh_dir}/config.json"
  else
    echo -e "  ${GREEN}Skipping doc selection (re-init). Run with existing known_docs.${NC}"
  fi

  # Always regenerate templates (this is the staleness fix)
  generate_grooming_standards "$kh_dir" "$project_dir"
  log "INFO" "Generated .kh/templates/GROOMING_STANDARDS.md"

  generate_local_delivery_template "$kh_dir" "$project_dir"
  log "INFO" "Generated .kh/templates/DELIVERY_HANDOFF_TEMPLATE.md"

  cp "${KH_PROTOCOLS}/EXECUTOR_STANDARDS.md" "${kh_dir}/templates/EXECUTOR_STANDARDS.md"
  log "INFO" "Copied .kh/templates/EXECUTOR_STANDARDS.md"

  # Copy additional templates (checklist, patterns, etc.)
  for tmpl in JM_COMPLETENESS_CHECKLIST.md JM_PATTERNS.md; do
    if [[ -f "${KH_TEMPLATES}/${tmpl}" ]]; then
      cp "${KH_TEMPLATES}/${tmpl}" "${kh_dir}/templates/${tmpl}"
      log "INFO" "Copied .kh/templates/${tmpl}"
    fi
  done

  # Update template version
  local temp_file; temp_file=$(mktemp)
  jq '.template_version = "0.2.0"' "${kh_dir}/config.json" > "$temp_file" && mv "$temp_file" "${kh_dir}/config.json"

  # Journey Mappings — look for existing, create from template if missing
  local jm_found=false
  for jm_path in \
    "${project_dir}/docs/JOURNEY_MAPPINGS.md" \
    "${project_dir}/JOURNEY_MAPPINGS.md" \
    "${project_dir}/docs/journey_mappings.md" \
    "${project_dir}/docs/journey-mappings.md"; do
    if [[ -f "$jm_path" ]]; then
      jm_found=true
      log "INFO" "Found existing journey mappings catalog: ${jm_path}"
      break
    fi
  done
  if [[ "$jm_found" == "false" ]]; then
    cp "${KH_TEMPLATES}/JOURNEY_MAPPINGS_TEMPLATE.md" "${project_dir}/docs/JOURNEY_MAPPINGS.md"
    log "INFO" "Created docs/JOURNEY_MAPPINGS.md from template"
    success "Created journey mappings catalog: docs/JOURNEY_MAPPINGS.md"
  fi

  # User Flow Catalog — look for existing, create from template if missing
  local user_flows_found=false
  for uf_path in \
    "${project_dir}/docs/USER_FLOWS.md" \
    "${project_dir}/USER_FLOWS.md" \
    "${project_dir}/docs/user_flows.md" \
    "${project_dir}/docs/user-flows.md"; do
    if [[ -f "$uf_path" ]]; then
      user_flows_found=true
      log "INFO" "Found existing user flow catalog: ${uf_path}"
      break
    fi
  done
  if [[ "$user_flows_found" == "false" ]]; then
    cp "${KH_TEMPLATES}/USER_FLOWS_TEMPLATE.md" "${project_dir}/docs/USER_FLOWS.md"
    log "INFO" "Created docs/USER_FLOWS.md from template"
    success "Created user flow catalog: docs/USER_FLOWS.md"
  fi

  # Architecture doc — look for existing, create from template if missing
  local arch_found=false
  for arch_path in \
    "${project_dir}/docs/ARCHITECTURE.md" \
    "${project_dir}/ARCHITECTURE.md" \
    "${project_dir}/docs/ARCHITECTURE_STATUS.md"; do
    if [[ -f "$arch_path" ]]; then
      arch_found=true
      log "INFO" "Found existing architecture doc: ${arch_path}"
      break
    fi
  done
  if [[ "$arch_found" == "false" ]]; then
    local project_name
    project_name=$(basename "$project_dir")
    sed "s/\[PROJECT_NAME\]/${project_name}/" "${KH_TEMPLATES}/ARCHITECTURE_TEMPLATE.md" \
      > "${project_dir}/docs/ARCHITECTURE.md"
    log "INFO" "Created docs/ARCHITECTURE.md from template"
    success "Created architecture doc: docs/ARCHITECTURE.md"
  fi

  LOG_FILE="${kh_dir}/kh.log"
  log "INFO" "ThousandHand initialized in ${project_dir} [context: ${current_context}]"
  success "ThousandHand ready [${current_context}]"
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

  jq --arg id "$safe_name" --arg nm "$name" --arg file "${safe_name}.md" --arg ts "$timestamp" --argjson pri "$next_priority" \
     '.items += [{
       "id": $id, "name": $nm, "draft_file": $file, "state": "draft", "phase": null,
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

  # --- PRE-FLOW: Raw → Breakdown → Draft ---
  local raw_pending=0 raw_done=0
  if [[ -f "$STATE_FILE" ]]; then
    raw_pending=$(jq '[.raw_items // [] | .[] | select(.status == "pending")] | length' "$STATE_FILE" 2>/dev/null || echo 0)
    raw_done=$(jq '[.raw_items // [] | .[] | select(.status == "broken_down")] | length' "$STATE_FILE" 2>/dev/null || echo 0)
  fi

  echo -e "📥 ${YELLOW}RAW${NC} (${raw_pending} items):"
  if [[ $raw_pending -gt 0 ]]; then
    jq -r '.raw_items // [] | .[] | select(.status == "pending") | "   \(.id)  → kh breakdown \"\(.id)\""' "$STATE_FILE" 2>/dev/null || true
  else
    echo "   (empty)"
  fi
  echo ""

  echo -e "🔀 ${YELLOW}BROKEN DOWN${NC} (${raw_done} items):"
  if [[ $raw_done -gt 0 ]]; then
    jq -r '.raw_items // [] | .[] | select(.status == "broken_down") | "   \(.id)  → \(.promoted_drafts | length) drafts promoted"' "$STATE_FILE" 2>/dev/null || true
  else
    echo "   (empty)"
  fi
  echo ""

  # --- SCOPE-DEFERRED: JM_NEW items parked during active execution ---
  local scope_deferred_total=0
  scope_deferred_total=$(jq '[.raw_items // [] | .[] | .deferred_scope_count // 0] | add // 0' "$STATE_FILE" 2>/dev/null || echo 0)
  if [[ $scope_deferred_total -gt 0 ]]; then
    echo -e "⟲ ${CYAN}SCOPE-DEFERRED${NC} (${scope_deferred_total} items):"
    # List IDs from deferred_scope files
    for dsf in "${RAW_DIR}"/*_deferred_scope.md; do
      [[ -f "$dsf" ]] || continue
      grep '^\- \*\*ID:\*\*' "$dsf" 2>/dev/null | sed 's/.*\*\*ID:\*\* /   /' || true
    done
    echo -e "   ${CYAN}(use kh promote \"id\" to activate)${NC}"
    echo ""
  fi

  # --- EXECUTION FLOW: Draft → Groom → Develop → Update → Complete ---
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
        draft)      ls -1 "$DRAFT_DIR"/*.md 2>/dev/null | xargs -I {} basename {} .md | sed 's/^/   /' ;;
        complete)   ls -1 "$COMPLETE_DIR"/*.md 2>/dev/null | xargs -I {} basename {} .md | sed 's/^/   /' ;;
        grooming)   jq -r '.items[] | select(.state == "developing" and .phase == "grooming") | "   \(.id)"' "$STATE_FILE" ;;
        developing) jq -r '.items[] | select(.state == "developing" and .phase == "development") | "   \(.id)"' "$STATE_FILE" ;;
        updating)   jq -r '.items[] | select(.state == "developing" and .phase == "update") | "   \(.id)"' "$STATE_FILE" ;;
      esac
    else
      echo "   (empty)"
    fi
    echo ""
  done

  # User Flow Coverage
  if [[ -f "$CONFIG_FILE" ]]; then
    local project_root_for_flows
    local raw_root
    raw_root=$(jq -r '.project_root' "$CONFIG_FILE" 2>/dev/null)
    if [[ "$raw_root" == /* ]]; then
      project_root_for_flows="$raw_root"
    else
      project_root_for_flows="$(cd "${KH_DIR}/.." && cd "$raw_root" && pwd)"
    fi
    local uf_file="${project_root_for_flows}/docs/USER_FLOWS.md"
    if [[ -f "$uf_file" ]]; then
      local defined implemented tested verified
      defined=$(grep -c '^\- \*\*ID:\*\*' "$uf_file" 2>/dev/null || echo 0)
      implemented=$(grep -c 'IMPLEMENTED\|TESTED\|VERIFIED' "$uf_file" 2>/dev/null || echo 0)
      tested=$(grep -c 'TESTED\|VERIFIED' "$uf_file" 2>/dev/null || echo 0)
      verified=$(grep -c 'VERIFIED' "$uf_file" 2>/dev/null || echo 0)
      echo -e "${CYAN}USER FLOWS:${NC} ${defined} defined | ${implemented} implemented | ${tested} tested | ${verified} verified"
      echo ""
    fi
  fi

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

  # Read execution context
  local exec_context
  exec_context=$(jq -r '.execution_context // "local"' "$CONFIG_FILE")

  # Resolve templates
  local grooming_standards="${KH_DIR}/templates/GROOMING_STANDARDS.md"
  [[ -f "$grooming_standards" ]] || grooming_standards="${KH_TEMPLATES}/MASTER_GROOMING_STANDARDS.md"
  local del_template="${KH_DIR}/templates/DELIVERY_HANDOFF_TEMPLATE.md"
  [[ -f "$del_template" ]] || del_template="${KH_TEMPLATES}/MASTER_DELIVERY_HANDOFF_TEMPLATE.md"
  local executor_standards="${KH_DIR}/templates/EXECUTOR_STANDARDS.md"
  [[ -f "$executor_standards" ]] || executor_standards="${KH_PROTOCOLS}/EXECUTOR_STANDARDS.md"

  # Locate user flow catalog
  local user_flows_path=""
  for uf in "${PROJECT_ROOT}/docs/USER_FLOWS.md" "${PROJECT_ROOT}/USER_FLOWS.md"; do
    [[ -f "$uf" ]] && user_flows_path="$uf" && break
  done

  local doc_section
  doc_section=$(build_doc_section "$CONFIG_FILE" "$PROJECT_ROOT")

  # User flow reference section for prompt
  local flow_section=""
  if [[ -n "$user_flows_path" ]]; then
    flow_section="- User flow catalog: ${user_flows_path}

## USER FLOW MANAGEMENT (during GROOMING)
1. Read the user flow catalog (docs/USER_FLOWS.md)
2. Determine: does this item describe a user journey, a buildable task, or both?
   - If JOURNEY: define the flow(s) in the catalog, derive implementation tasks
   - If TASK: check which existing flows it serves — create new flows if this task introduces new user journeys
   - If INFRASTRUCTURE/CHORE: mark as flow-independent, proceed without flow association
3. Update docs/USER_FLOWS.md with any new or modified flows
4. Include flow references in your success criteria"
  fi

  # Context-specific environment instructions
  local context_instructions=""
  case "$exec_context" in
    local)
      context_instructions="ENVIRONMENT: LOCAL — Use SQLite, local file storage, mock integrations. Everything at localhost. See Executor Standards Section 2.1." ;;
    mixed)
      context_instructions="ENVIRONMENT: MIXED — Some services are production, some local. USE THE ACTUAL DATABASE AND SERVICES that the project has configured. Check .env files and existing integration code to determine what's real vs mocked. Seed data into the REAL database, not into mocks or demo modes. If Supabase is configured, query Supabase. If S3 is configured, use S3. See Executor Standards Section 2.2." ;;
    production)
      context_instructions="ENVIRONMENT: PRODUCTION — All services are production. Every mutation is real. Seed data must be clearly identifiable (test_* prefix) and cleanly removable. Extra caution on migrations and data changes. See Executor Standards Section 2.3." ;;
  esac

  # Uppercase context for display (bash 3.2 compatible — no ${var^^})
  local exec_context_upper
  exec_context_upper=$(echo "$exec_context" | tr '[:lower:]' '[:upper:]')

  # Consolidated 3-phase prompt
  local prompt="> BEST EFFORTS / AGGRESSIVE EXECUTION. Move fast, assume and document.
> [EXECUTION_CONTEXT: ${exec_context_upper}]
> ${context_instructions}

You are processing a task through 3 phases in a SINGLE SESSION:
GROOMING -> DEVELOPMENT -> UPDATE.
Do NOT create a separate grooming handoff file — analyze inline.

INPUT DRAFT:
${draft_content}

REFERENCE FILES (read at start):
- Grooming standards: ${grooming_standards}
- Executor standards (build philosophy + TDD protocol): ${executor_standards}
- Delivery handoff template: ${del_template}
- Project ROADMAP: ${DOCS_PATH}/ROADMAP.md
- Project TECH_STACK: ${DOCS_PATH}/TECH_STACK.md
- Project ARCHITECTURE: ${DOCS_PATH}/ARCHITECTURE.md
${flow_section}

## PHASE 1: GROOMING
1. Read grooming standards + executor standards + project docs
2. TRIAGE: classify as FEATURE/MAJOR_FIX/SMALL_FIX/DOCUMENTATION
3. Emit: [TRIAGE: <classification>]
4. Analyze: objective, scope, success criteria, architecture (WHAT not HOW)
5. User flow management: read catalog, classify item, update catalog, map flows
6. Validate scope (>5 files -> note for consideration)
7. Emit: [PHASE: GROOMING_COMPLETE]

## PHASE 2: DEVELOPMENT
Follow EXECUTOR_STANDARDS for build order and TDD protocol:
1. Read ARCHITECTURE.md, understand what exists
2. Implement based on grooming analysis (data layer -> app layer -> layout -> style)
3. Write tests FIRST (per triage level):
   - For each referenced user flow: write end-to-end Playwright test covering the full journey
   - For new features: unit tests for logic + browser tests for UX
   - For fixes: regression tests for affected areas
4. Run ALL tests via bash runner -> read summary
5. For any failure: read error, fix code, re-run (max 3 attempts per failure)
6. Loop until ALL PASS or retry ceiling hit
7. Create DELIVERY_HANDOFF -> ${HANDOFFS_PATH}/DELIVERY_${feature_name}.md
8. Emit: [PHASE: DEVELOPMENT_COMPLETE]

## PHASE 3: UPDATE
${doc_section}
- Update docs/ARCHITECTURE.md with delivery breadcrumbs (source paths, data models, tests, decisions)
- Update docs/USER_FLOWS.md flow statuses (DEFINED -> IMPLEMENTED -> TESTED as appropriate)
(If DOCUMENTATION triage: lightweight — just mark DELIVERY_HANDOFF as UPDATES_COMPLETE)
Emit: [PHASE: UPDATE_COMPLETE]

COMPLETE: DELIVERY_${feature_name}.md"

  check_stop_sentinel

  log "INFO" "Launching consolidated session for: $id"

  local stream_file="${KH_DIR}/sessions/${id}_stream.jsonl"
  echo "$stream_file" > "${KH_DIR}/active_stream"

  # Write prompt to temp file — avoids CLI argument length limits and quoting issues
  local prompt_file="${KH_DIR}/sessions/${id}_prompt.txt"
  printf '%s' "$prompt" > "$prompt_file"

  touch "$stream_file"
  start_phase_monitor "$id" "$stream_file"

  local exit_code=0
  ( cd "$PROJECT_ROOT" && claude -p \
    --model "$MODEL" \
    --dangerously-skip-permissions \
    --verbose --output-format stream-json \
    --max-turns 100 \
    < "$prompt_file" \
  ) > "$stream_file" 2>&1 || exit_code=$?

  stop_phase_monitor
  rm -f "${KH_DIR}/active_stream" "$prompt_file"

  # Surface errors to terminal if session produced no output
  if [[ $exit_code -ne 0 && ! -s "$stream_file" ]]; then
    warn "Claude session exited with code $exit_code but produced no output"
  elif [[ $exit_code -ne 0 ]]; then
    local first_error
    first_error=$(head -5 "$stream_file" | grep -i "error" || true)
    [[ -n "$first_error" ]] && warn "Claude error: $first_error"
  fi

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

  # --- Check if this is a scope-deferred item (not in state.json yet) ---
  local current_state
  current_state=$(jq -r --arg id "$safe_name" '.items[] | select(.id == $id) | .state // empty' "$STATE_FILE" 2>/dev/null)

  if [[ -z "$current_state" ]]; then
    # Not in state.json — check if it's in a deferred_scope file
    local found_scope_file=""
    local found_draft_content=""
    for dsf in "${RAW_DIR}"/*_deferred_scope.md; do
      [[ -f "$dsf" ]] || continue
      if grep -q "^\- \*\*ID:\*\* ${safe_name}$" "$dsf" 2>/dev/null; then
        found_scope_file="$dsf"
        # Extract stored draft content between ``` markers after the matching ID section
        found_draft_content=$(awk -v id="$safe_name" '
          /^- \*\*ID:\*\*/ && $0 ~ id { found=1; next }
          found && /^### Stored Draft Content/ { capture=1; next }
          capture && /^```$/ && !started { started=1; next }
          capture && started && /^```$/ { exit }
          capture && started { print }
        ' "$dsf")
        break
      fi
    done

    if [[ -z "$found_scope_file" ]]; then
      error "Item '${name}' not found in state.json or any deferred_scope file"
      exit 1
    fi

    # Promote from scope-deferred to draft
    echo -e "${BLUE}Promoting scope-deferred item: ${safe_name}${NC}"

    if [[ -n "$found_draft_content" ]]; then
      printf '%s\n' "$found_draft_content" > "${DRAFT_DIR}/${safe_name}.md"
    else
      warn "Could not extract stored draft content — creating placeholder draft"
      echo "# ${safe_name} (promoted from scope-deferred)" > "${DRAFT_DIR}/${safe_name}.md"
    fi

    # Add to state.json
    local temp_file; temp_file=$(mktemp)
    local timestamp; timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local next_priority; next_priority=$(jq '.items | length' "$STATE_FILE")
    jq --arg id "$safe_name" --arg file "${safe_name}.md" --arg ts "$timestamp" \
       --argjson pri "$next_priority" \
       '.items += [{
         "id": $id, "name": $id, "draft_file": $file, "state": "draft", "phase": null,
         "session_id": null, "delivery_handoff": null, "triage": null,
         "priority": $pri, "tokens": {}, "started_at": $ts,
         "completed_at": null, "error": null, "raw_source": "scope-deferred"
       }] | .last_updated = $ts' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

    success "Promoted from scope-deferred → draft: ${safe_name}"
    echo -e "  Draft: ${BLUE}draft/${safe_name}.md${NC}"
    return
  fi

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

  # Write resume prompt to temp file
  local prompt_file="${KH_DIR}/sessions/${safe_name}_resume_prompt.txt"
  printf '%s' "$resume_prompt" > "$prompt_file"

  start_phase_monitor "$safe_name" "$stream_file"

  local exit_code=0
  ( cd "$PROJECT_ROOT" && claude --resume "$session_id" \
    -p \
    --dangerously-skip-permissions \
    --verbose --output-format stream-json \
    < "$prompt_file" \
  ) >> "$stream_file" 2>&1 || exit_code=$?

  stop_phase_monitor
  rm -f "${KH_DIR}/active_stream" "$prompt_file"

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

cmd_close() {
  load_config
  local modifier="${1:-}"
  local close_id="closing-ceremony"
  [[ -n "$modifier" ]] && close_id="closing-ceremony-${modifier}"
  local safe_name; safe_name=$(to_safe_name "$close_id")
  local filename="${safe_name}.md"
  local feature_name; feature_name=$(to_feature_name "$safe_name")

  log "INFO" "Initiating closing ceremony: ${safe_name}"
  header
  echo -e "${MAGENTA}                   CLOSING CEREMONY                          ${NC}"
  header
  echo ""

  # Check no active session
  local current_active
  current_active=$(jq -r '.active_session // empty' "$STATE_FILE")
  if [[ -n "$current_active" && "$current_active" != "null" ]]; then
    error "Session already active: $current_active. Wait for it to finish."
    return 1
  fi

  # Create closing ceremony draft
  echo "CLOSING CEREMONY: Comprehensive review, test gap analysis, and UAT preparation." > "${DRAFT_DIR}/${filename}"

  # Add to state
  local timestamp next_priority temp_file
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  next_priority=$(jq '.items | length' "$STATE_FILE")
  temp_file=$(mktemp)
  jq --arg id "$safe_name" --arg file "$filename" --arg ts "$timestamp" --argjson pri "$next_priority" \
     '.items += [{
       "id": $id, "draft_file": $file, "state": "draft", "phase": null,
       "session_id": null, "delivery_handoff": null, "triage": "CLOSING_CEREMONY",
       "priority": $pri, "tokens": {}, "started_at": $ts,
       "completed_at": null, "error": null
     }] | .last_updated = $ts' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  # Move to developing
  mv "${DRAFT_DIR}/${filename}" "${DEV_DIR}/"
  update_item "$safe_name" "state" "developing"
  update_item "$safe_name" "phase" "discovery"
  update_global "active_session" "$safe_name"

  # Resolve templates
  local closing_ceremony_doc="${KH_PROTOCOLS}/CLOSING_CEREMONY.md"
  [[ -f "$closing_ceremony_doc" ]] || closing_ceremony_doc="${DOCS_PATH}/CLOSING_CEREMONY.md"
  local executor_standards="${KH_DIR}/templates/EXECUTOR_STANDARDS.md"
  [[ -f "$executor_standards" ]] || executor_standards="${KH_PROTOCOLS}/EXECUTOR_STANDARDS.md"

  # Locate user flow catalog
  local user_flows_path=""
  for uf in "${PROJECT_ROOT}/docs/USER_FLOWS.md" "${PROJECT_ROOT}/USER_FLOWS.md"; do
    [[ -f "$uf" ]] && user_flows_path="$uf" && break
  done

  # Read execution context for closing ceremony
  local exec_context
  exec_context=$(jq -r '.execution_context // "local"' "$CONFIG_FILE")
  local exec_context_upper
  exec_context_upper=$(echo "$exec_context" | tr '[:lower:]' '[:upper:]')

  # Build the closing ceremony prompt
  local prompt="> CLOSING CEREMONY — Comprehensive review + test gap analysis + UAT preparation.
> [EXECUTION_CONTEXT: ${exec_context_upper}]

You are executing a CLOSING CEREMONY for this project. This is NOT a feature build. This is a comprehensive review of everything that has been built, with the goal of preparing a UAT delivery package for the system owner.

IMPORTANT: Execution context is ${exec_context_upper}. Seed data and tests must target the ACTUAL infrastructure the project uses (see Executor Standards Section 2 for context-specific rules).

REFERENCE FILES (read ALL at start):
- Closing ceremony requirements: ${closing_ceremony_doc}
- Executor standards: ${executor_standards}
- Project ARCHITECTURE: ${DOCS_PATH}/ARCHITECTURE.md
- User flow catalog: ${user_flows_path:-docs/USER_FLOWS.md}
- Delivery handoffs directory: ${HANDOFFS_PATH}/

## PHASE 1: DISCOVERY
1. Read ARCHITECTURE.md — understand what exists, what was built, what components are live
2. Read the user flow catalog (docs/USER_FLOWS.md) — inventory every defined flow
3. Read ALL delivery handoffs in ${HANDOFFS_PATH}/ — understand what was delivered
4. Inventory existing tests — what test files exist? What's their pass rate?
5. Emit: [CEREMONY: DISCOVERY_COMPLETE]

## PHASE 2: FLOW COVERAGE AUDIT
For EACH user flow in the catalog:
1. Does a test exist for this flow? (check test directories)
2. Does the test PASS? (run it)
3. If NO test exists → WRITE the test now (end-to-end Playwright covering the full journey)
4. If test FAILS → attempt fix (up to 3 retries per failure, per executor standards TDD protocol)
5. Update flow status in docs/USER_FLOWS.md: DEFINED → TESTED (or note gap)
6. Emit: [CEREMONY: TESTS_COMPLETE]

## PHASE 3: EXECUTION & RESULTS
1. Run the FULL test suite (all existing + newly created tests)
2. Generate test-results/summary.json (pass/fail per test, durations, error messages)
3. Create testing/closing-ceremony/RESULTS.md with:
   - Summary (total/passing/failing/skipped)
   - Results by risk level (CRITICAL/HIGH/MEDIUM/LOW)
   - Failing flows with diagnosis
   - Risk assessment
4. Emit: [CEREMONY: EXECUTION_COMPLETE]

## PHASE 4: UAT DELIVERY PACKAGE
1. Create seed script (testing/closing-ceremony/seed.*) — idempotent test data population
2. Create reset script (testing/closing-ceremony/reset.*) — clean removal of test data
3. Create UAT Guide (docs/delivery/UAT_GUIDE${modifier:+_${modifier}}.md) with:
   - What was built (summary)
   - How to start (copy-paste commands)
   - Test users with credentials
   - Manual walkthroughs for each CRITICAL/HIGH flow
   - Playwright replay commands
   - Known issues
4. Create GTM Requirements manifest (docs/delivery/GTM${modifier:+_${modifier}}.md)
5. Update docs/ARCHITECTURE.md with closing ceremony results
6. Emit: [CEREMONY: UAT_GUIDE_COMPLETE]
7. Emit: [CEREMONY: CLOSING_COMPLETE]

COMPLETE: UAT_GUIDE${modifier:+_${modifier}}.md"

  check_stop_sentinel

  log "INFO" "Launching closing ceremony session"

  local stream_file="${KH_DIR}/sessions/${safe_name}_stream.jsonl"
  echo "$stream_file" > "${KH_DIR}/active_stream"

  # Write prompt to temp file — avoids CLI argument length limits and quoting issues
  local prompt_file="${KH_DIR}/sessions/${safe_name}_prompt.txt"
  printf '%s' "$prompt" > "$prompt_file"

  touch "$stream_file"
  start_phase_monitor "$safe_name" "$stream_file"

  local exit_code=0
  ( cd "$PROJECT_ROOT" && claude -p \
    --model "$MODEL" \
    --dangerously-skip-permissions \
    --verbose --output-format stream-json \
    --max-turns 150 \
    < "$prompt_file" \
  ) > "$stream_file" 2>&1 || exit_code=$?

  stop_phase_monitor
  rm -f "${KH_DIR}/active_stream" "$prompt_file"

  # Surface errors to terminal if session produced no output
  if [[ $exit_code -ne 0 && ! -s "$stream_file" ]]; then
    warn "Claude session exited with code $exit_code but produced no output"
  elif [[ $exit_code -ne 0 ]]; then
    local first_error
    first_error=$(head -5 "$stream_file" | grep -i "error" || true)
    [[ -n "$first_error" ]] && warn "Claude error: $first_error"
  fi

  finalize_item "$safe_name" "$stream_file" "$exit_code" "false"
}

cmd_stop() {
  resolve_paths
  touch "${KH_DIR}/STOP"
  log "INFO" "Stop sentinel written"
  echo -e "${YELLOW}Stop sentinel written.${NC} KH will halt after the current Claude call finishes."
  echo "If stuck: ${BLUE}kill \$(pgrep -f 'kh.sh')${NC}"
}

# ═══════════════════════════════════════════════════════════
# RAW + BREAKDOWN (pre-flow)
# ═══════════════════════════════════════════════════════════

cmd_raw() {
  local subcmd="${1:-}"
  case "$subcmd" in
    list) cmd_raw_list ;;
    show)
      [[ -z "${2:-}" ]] && { echo "Usage: kh raw show \"name\""; exit 1; }
      cmd_raw_show "$2" ;;
    "")
      echo "Usage:"
      echo "  kh raw \"name\" <<< 'messy input'    # Intake from stdin"
      echo "  kh raw \"name\" < file.md             # Intake from file"
      echo "  kh raw list                          # List all raw inputs"
      echo "  kh raw show \"name\"                   # Show raw input + breakdown"
      ;;
    *)
      cmd_raw_add "$@" ;;
  esac
}

cmd_raw_add() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  mkdir -p "$RAW_DIR"
  local raw_file="${RAW_DIR}/${safe_name}.md"

  log "INFO" "Adding raw input: $name"

  local content
  [[ -t 0 ]] && echo -e "${YELLOW}Enter raw input (Ctrl+D when done):${NC}"
  content=$(cat)

  if [[ -z "$content" ]]; then
    error "No content provided."
    echo "  kh raw \"name\" <<< 'one-liner'"
    echo "  kh raw \"name\" < braindump.md"
    exit 1
  fi

  # Check for existing raw input with same name
  if [[ -f "$raw_file" ]]; then
    warn "Raw input '${safe_name}' already exists."
    read -p "Overwrite or create versioned? [overwrite/version] " choice
    case "$choice" in
      v|version)
        local version=2
        while [[ -f "${RAW_DIR}/${safe_name}_v${version}.md" ]]; do
          version=$((version + 1))
        done
        safe_name="${safe_name}_v${version}"
        raw_file="${RAW_DIR}/${safe_name}.md"
        ;;
      *) ;; # overwrite
    esac
  fi

  printf '%s\n' "$content" > "$raw_file"

  # Add/update raw_items in state.json
  local timestamp temp_file
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  temp_file=$(mktemp)

  # Check if item already exists in raw_items
  local exists
  exists=$(jq -r --arg id "$safe_name" '.raw_items // [] | map(select(.id == $id)) | length' "$STATE_FILE" 2>/dev/null)

  if [[ "$exists" -gt 0 ]]; then
    # Update existing
    jq --arg id "$safe_name" --arg ts "$timestamp" \
       '(.raw_items[] | select(.id == $id)).status = "pending" |
        (.raw_items[] | select(.id == $id)).breakdown_at = null |
        .last_updated = $ts' \
       "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
  else
    # Add new
    jq --arg id "$safe_name" --arg file "raw/${safe_name}.md" --arg ts "$timestamp" \
       '.raw_items = (.raw_items // []) + [{
         "id": $id, "raw_file": $file, "status": "pending",
         "breakdown_file": null, "promoted_drafts": [],
         "deferred_count": 0, "rejected_count": 0,
         "breakdown_at": null, "created_at": $ts
       }] | .last_updated = $ts' \
       "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
  fi

  log "INFO" "Raw input saved: $raw_file"
  success "Raw input saved: ${safe_name}"
  echo -e "  Next: ${BLUE}kh breakdown \"${safe_name}\"${NC}"
}

cmd_raw_list() {
  echo ""
  header
  echo -e "${BLUE}                       RAW INPUTS                            ${NC}"
  header
  echo ""

  local has_items=false
  if [[ -f "$STATE_FILE" ]]; then
    local raw_count
    raw_count=$(jq '.raw_items // [] | length' "$STATE_FILE" 2>/dev/null)
    if [[ "$raw_count" -gt 0 ]]; then
      has_items=true
      jq -r '.raw_items // [] | .[] |
        "\(if .status == "pending" then "📋" elif .status == "broken_down" then "✅" else "❓" end)  \(.id)\t[\(.status)]"' \
        "$STATE_FILE" 2>/dev/null
    fi
  fi

  if [[ "$has_items" == "false" ]]; then
    echo -e "  ${YELLOW}(no raw inputs)${NC}"
    echo ""
    echo "  Add one: kh raw \"name\" <<< 'brain dump here'"
  fi

  echo ""
  header
}

cmd_raw_show() {
  local name="$1"
  local safe_name; safe_name=$(to_safe_name "$name")
  local raw_file="${RAW_DIR}/${safe_name}.md"

  [[ -f "$raw_file" ]] || { error "No raw input found: ${safe_name}"; exit 1; }

  header
  echo -e "  ${YELLOW}Raw: ${safe_name}${NC}"
  header
  echo ""
  echo -e "${CYAN}── Raw Input ──${NC}"
  cat "$raw_file"
  echo ""

  local breakdown_file="${RAW_DIR}/${safe_name}_breakdown.md"
  if [[ -f "$breakdown_file" ]]; then
    echo -e "${CYAN}── Breakdown Report ──${NC}"
    cat "$breakdown_file"
    echo ""
  else
    echo -e "${YELLOW}Not yet broken down. Run: kh breakdown \"${safe_name}\"${NC}"
  fi

  local deferred_file="${RAW_DIR}/${safe_name}_deferred.md"
  if [[ -f "$deferred_file" ]]; then
    echo -e "${CYAN}── Deferred Items ──${NC}"
    cat "$deferred_file"
    echo ""
  fi

  local rejected_file="${RAW_DIR}/${safe_name}_rejected.md"
  if [[ -f "$rejected_file" ]]; then
    echo -e "${CYAN}── Rejected Items ──${NC}"
    cat "$rejected_file"
    echo ""
  fi
}

cmd_breakdown() {
  local name="$1"
  local dry_run=false
  [[ "${2:-}" == "--dry-run" ]] && dry_run=true

  local safe_name; safe_name=$(to_safe_name "$name")
  local raw_file="${RAW_DIR}/${safe_name}.md"

  [[ -f "$raw_file" ]] || { error "No raw input found: ${safe_name}"; exit 1; }

  log "INFO" "Running breakdown on: ${safe_name}${dry_run:+ (dry-run)}"
  echo -e "${BLUE}Breaking down: ${safe_name}${NC}"
  [[ "$dry_run" == "true" ]] && echo -e "${YELLOW}(dry-run — no files will be created)${NC}"

  local raw_content
  raw_content=$(cat "$raw_file")

  # Gather context — JMs, UFs, existing drafts, completions
  local jm_context="(no journey mappings found)"
  for jm_path in "${PROJECT_ROOT}/docs/JOURNEY_MAPPINGS.md" "${DOCS_PATH}/JOURNEY_MAPPINGS.md"; do
    [[ -f "$jm_path" ]] && jm_context=$(cat "$jm_path") && break
  done

  local uf_context="(no user flows found)"
  for uf_path in "${PROJECT_ROOT}/docs/USER_FLOWS.md" "${PROJECT_ROOT}/USER_FLOWS.md"; do
    [[ -f "$uf_path" ]] && uf_context=$(cat "$uf_path") && break
  done

  local drafts_list=""
  drafts_list=$(ls -1 "$DRAFT_DIR"/*.md 2>/dev/null | xargs -I {} basename {} .md | tr '\n' ', ' || echo "(none)")
  [[ -z "$drafts_list" ]] && drafts_list="(none)"

  local complete_list=""
  complete_list=$(ls -1 "$COMPLETE_DIR"/*.md 2>/dev/null | xargs -I {} basename {} .md | tr '\n' ', ' || echo "(none)")
  [[ -z "$complete_list" ]] && complete_list="(none)"

  # Read checklist for heuristic reference
  local checklist_context=""
  local checklist_file="${KH_DIR}/templates/JM_COMPLETENESS_CHECKLIST.md"
  [[ -f "$checklist_file" ]] || checklist_file="${KH_TEMPLATES}/JM_COMPLETENESS_CHECKLIST.md"
  [[ -f "$checklist_file" ]] && checklist_context=$(cat "$checklist_file")

  # Gather previously deferred items for re-evaluation
  local deferred_context="(none)"
  local deferred_files
  deferred_files=$(ls -1 "${RAW_DIR}"/*_deferred.md 2>/dev/null || true)
  if [[ -n "$deferred_files" ]]; then
    deferred_context=""
    while IFS= read -r df; do
      local df_name
      df_name=$(basename "$df")
      deferred_context+="--- From: ${df_name} ---
$(cat "$df")
"
    done <<< "$deferred_files"
  fi

  # Gather previously scope-deferred items for re-evaluation
  local deferred_scope_context="(none)"
  local deferred_scope_files
  deferred_scope_files=$(ls -1 "${RAW_DIR}"/*_deferred_scope.md 2>/dev/null || true)
  if [[ -n "$deferred_scope_files" ]]; then
    deferred_scope_context=""
    while IFS= read -r dsf; do
      local dsf_name
      dsf_name=$(basename "$dsf")
      deferred_scope_context+="--- From: ${dsf_name} ---
$(cat "$dsf")
"
    done <<< "$deferred_scope_files"
  fi

  # Determine if active JM scope exists (for post-classification scope gating)
  local has_scope=false
  if has_active_jm_scope "$jm_context"; then
    has_scope=true
    log "INFO" "Active JM scope detected — JM_NEW items will be scope-deferred"
  fi

  # Build the breakdown prompt
  local prompt="> BREAKDOWN ANALYSIS — Split raw input into discrete, actionable items.
> You are NOT grooming. You are NOT implementing. You are TRIAGING.
> Work TOP-DOWN: JM → UF → Task.

## RAW INPUT
${raw_content}

## CONTEXT — Known Journey Mappings
${jm_context}

## CONTEXT — Known User Flows
${uf_context}

## CONTEXT — Existing Drafts in Queue
${drafts_list}

## CONTEXT — Already Completed Items
${complete_list}

## CONTEXT — Previously Deferred Items
${deferred_context}

## CONTEXT — Previously Scope-Deferred Items
${deferred_scope_context}

## SEMANTIC GROUPING (pre-classification step)

Before classifying individual items, read the raw input for semantic structure. Look for lines
that serve as TOPIC DECLARATIONS — broad statements that introduce a feature area — followed
by lines that describe SUB-OPERATIONS within that topic.

Signals that indicate parent-child relationships (any of these, not all required):
- A broad feature name followed by specific actions (e.g., 'ADMIN LAB ORDERS' followed by 'SIGN,' 'SEND,' 'VIEW')
- A line that names a workflow followed by lines that describe steps in that workflow
- A labeled section (e.g., 'CONSENT WORKFLOW:') followed by actor-specific details
- Lines that only make sense in the context of the line above them

When you detect a parent-child structure:
- The parent line becomes the GROUP TITLE, not a standalone observation
- The child lines become OBSERVATIONS within that group
- The resulting draft should frame these as a workflow or feature with named operations —
  not as independent items that happen to be grouped

This is semantic, not format-based. Do NOT rely on indentation, bullet characters, or markdown
syntax. The raw input may have inconsistent formatting from a notes app — tabs vs spaces,
missing bullets, mixed nesting. Read for MEANING, not for structure.

## CLASSIFICATION RULES

For each DISTINCT observation or request in the raw input:
1. Does it map to a known JM? Which step?
2. Within that step, does it map to a known UF? Which one?
3. If it's a new UF within an existing JM, say so.
4. If it doesn't map to any JM: is it a new JM, a CHORE, VAGUE, or NON_IMPLEMENTATION?

AMBIGUITY RULE: If a line could be either a section header OR a standalone observation,
AND it has no clearly related sub-items following it, err toward classifying it as a
standalone item. Let grooming merge it if redundant. Brain dumps often have labels like
'CROSS-OP' or 'APP UPDATES' that look like headers but actually represent a distinct
feature request. When in doubt, promote — don't absorb.
HOWEVER: If the line IS followed by sub-items that only make sense in its context,
treat it as a topic declaration and group the sub-items under it (see SEMANTIC GROUPING above).

Categories (assign exactly one per item):
- JM_EXISTING_UF — maps to known JM + known UF → promote to draft
- JM_NEW_UF — maps to known JM but is a new user flow → promote to draft
- JM_NEW — entirely new journey → promote to draft as JM definition
- CHORE — infrastructure, refactor, DX, rename → promote to draft
- FUTURE_JM — good idea but not current scope → defer
- DEFERRED_PROMOTED — previously deferred item that NOW maps to a known JM → promote to draft
- REDUNDANCY — already covered by existing draft or completed item → note only
- VAGUE — cannot determine what this means → reject for human review
- NON_IMPLEMENTATION — not a software task → reject

## DEFERRED RE-EVALUATION

Check the 'Previously Deferred Items' context above. For each deferred item, ask:
does it NOW map to a known JM that exists in the Journey Mappings context?
If yes, re-classify it as DEFERRED_PROMOTED and include it in the breakdown output
as a promoted item. Add it to the appropriate execution group or as standalone.
If it still doesn't map, leave it deferred — do NOT re-defer it (it's already in a deferred file).

Also check the 'Previously Scope-Deferred Items' context above. These were classified as
JM_NEW but deferred because active JM execution was in progress. For each scope-deferred item:
does its journey NOW appear as an active JM (IMPLEMENTED or IN PROGRESS) in Journey Mappings?
If yes, re-classify it as DEFERRED_PROMOTED and include it in the breakdown output.
If it still doesn't match an active JM, leave it — do NOT re-defer it.

## GROUPING RULES

After categorizing, suggest execution groups. Items that share the same JM + Step + Actor
should be grouped into a SINGLE draft (prevents over-splitting into tiny tasks).
Each group becomes one draft file. Standalone items (CHORE, unique step) get their own draft.

MERGE HINTS: If two groups serve the same system concern (e.g., both are 'system sends
notifications to client' but at different JM steps), keep them as separate drafts but add
a note in the report: 'Groups X and Y could be merged during grooming if scope allows.'
This helps grooming make informed merge decisions without breakdown overstepping.

## JM COMPLETENESS CHECKLIST (use as heuristic)

Use these layers to help classify items:
- Layer 1 (Actors): Does item introduce a new actor? → might be new JM
- Layer 2 (States): Does item describe a missing entity state? → gap in existing JM
- Layer 3 (Sad paths): Is it a 'what if they don't?' scenario? → existing step's sad path
- Layer 5 (Other screen): Is it about what another actor sees? → cross-actor visibility gap

## OUTPUT FORMAT

Produce TWO sections:

### SECTION 1: Markdown Breakdown Report
A human-readable report with:
- Summary line: \"Items found: N | Promoted: N | Deferred: N | Rejected: N | Redundant: N\"
  IMPORTANT: Count items AFTER full classification, not before. The summary counts MUST
  match the actual rows in your table. Promoted = items going to draft (groups + standalone).
  Total = Promoted + Deferred + Rejected. Redundant is a separate note count (not added to total).
- Each item numbered: title, category, maps_to, reasoning (1 sentence)
- Suggested execution groups with group letter and member items
- Deferred items with reasoning
- Rejected items with reasoning

### SECTION 2: JSON Block
After the markdown, output a JSON block between markers. This MUST be valid JSON.

[BREAKDOWN_JSON]
{
  \"summary\": { \"total\": 0, \"promoted\": 0, \"deferred\": 0, \"rejected\": 0, \"redundant\": 0 },
  \"groups\": [
    {
      \"id\": \"A\",
      \"label\": \"Human-readable group label\",
      \"draft_id\": \"safe-kebab-case-id\",
      \"item_numbers\": [1, 2],
      \"category\": \"JM_EXISTING_UF\",
      \"maps_to\": \"JM1, Step 1, Client UX\",
      \"maps_to_uf\": \"UF-C01 or null if new\",
      \"draft_content\": \"# Group A: Label\n\nSource: raw/${safe_name}.md\nCategory: ...\nMaps to: ...\n\n## Observations\n\n### Item 1: title\nOriginal text...\n\n### Item 2: title\nOriginal text...\"
    }
  ],
  \"standalone\": [
    {
      \"draft_id\": \"safe-kebab-case-id\",
      \"label\": \"Human-readable standalone label\",
      \"item_number\": 1,
      \"category\": \"CHORE\",
      \"maps_to\": \"JM1 (general)\",
      \"maps_to_uf\": null,
      \"draft_content\": \"# title\n\nSource: raw/${safe_name}.md\nCategory: CHORE\nMaps to: ...\n\nOriginal text...\"
    }
  ],
  \"deferred\": [
    { \"item_number\": 8, \"title\": \"...\", \"category\": \"FUTURE_JM\", \"reasoning\": \"...\" }
  ],
  \"rejected\": [
    { \"item_number\": 9, \"title\": \"...\", \"category\": \"VAGUE\", \"reasoning\": \"...\" }
  ]
}
[/BREAKDOWN_JSON]

IMPORTANT:
- draft_id values must be unique, lowercase, kebab-case
- draft_content must include the original observation text (don't lose the user's words)
- draft_content must include the category and maps_to metadata at the top
- Do NOT include acceptance criteria or implementation details — that's grooming's job
- Keep reasoning to 1-2 sentences per item"

  # Write prompt to temp file (avoids argument length limits)
  local prompt_file="${KH_DIR}/sessions/${safe_name}_breakdown_prompt.txt"
  printf '%s' "$prompt" > "$prompt_file"

  echo -e "  ${CYAN}Running AI analysis...${NC}"

  local output exit_code=0
  output=$( cd "$PROJECT_ROOT" && claude -p \
    --model "${MODEL}" \
    --max-turns 3 \
    < "$prompt_file" \
  ) || exit_code=$?

  rm -f "$prompt_file"

  if [[ $exit_code -ne 0 || -z "$output" ]]; then
    error "Breakdown failed (exit code: $exit_code)"
    [[ -n "$output" ]] && echo "$output" | tail -20
    return 1
  fi

  # --- DRY RUN: just print and exit ---
  if [[ "$dry_run" == "true" ]]; then
    echo ""
    echo "$output" | sed '/\[BREAKDOWN_JSON\]/,/\[\/BREAKDOWN_JSON\]/d'
    echo ""
    success "Dry run complete — no files created."
    return 0
  fi

  # --- Extract markdown report (everything before [BREAKDOWN_JSON]) ---
  local report
  report=$(echo "$output" | sed '/\[BREAKDOWN_JSON\]/,$d')
  echo "$report" > "${RAW_DIR}/${safe_name}_breakdown.md"
  log "INFO" "Breakdown report saved: raw/${safe_name}_breakdown.md"

  # --- Extract JSON block ---
  local json_block
  json_block=$(echo "$output" | sed -n '/\[BREAKDOWN_JSON\]/,/\[\/BREAKDOWN_JSON\]/p' | grep -v '\[BREAKDOWN_JSON\]\|\[\/BREAKDOWN_JSON\]')

  if [[ -z "$json_block" ]] || ! echo "$json_block" | jq empty 2>/dev/null; then
    warn "Could not parse breakdown JSON. Report saved but no drafts auto-promoted."
    warn "Review: ${RAW_DIR}/${safe_name}_breakdown.md"
    echo "$output" > "${RAW_DIR}/${safe_name}_breakdown.md"  # Save full output
    return 1
  fi

  # --- Create draft files from groups and standalone items ---
  local promoted_ids=()
  local scope_deferred_ids=()
  local scope_deferred_entries=()
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Helper: promote an item to draft or scope-defer it
  _promote_or_scope_defer() {
    local draft_id="$1" draft_content="$2" category="$3" label="$4" maps_to="$5"

    # --- SCOPE GATING: JM_NEW + active scope → deferred_scope ---
    if [[ "$category" == "JM_NEW" && "$has_scope" == "true" ]]; then
      scope_deferred_ids+=("$draft_id")
      scope_deferred_entries+=("$(printf '%s\t%s\t%s\t%s' "$draft_id" "$label" "$maps_to" "$draft_content")")
      echo -e "  ${CYAN}⟲${NC} Scope-deferred: ${draft_id} [JM_NEW → active scope exists]"
      return
    fi

    # --- Normal promotion to draft ---
    printf '%s\n' "$draft_content" > "${DRAFT_DIR}/${draft_id}.md"

    local temp_file; temp_file=$(mktemp)
    local next_priority; next_priority=$(jq '.items | length' "$STATE_FILE")
    jq --arg id "$draft_id" --arg file "${draft_id}.md" --arg ts "$timestamp" \
       --argjson pri "$next_priority" --arg src "$safe_name" \
       '.items += [{
         "id": $id, "name": $id, "draft_file": $file, "state": "draft", "phase": null,
         "session_id": null, "delivery_handoff": null, "triage": null,
         "priority": $pri, "tokens": {}, "started_at": $ts,
         "completed_at": null, "error": null, "raw_source": $src
       }] | .last_updated = $ts' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

    promoted_ids+=("$draft_id")
    echo -e "  ${GREEN}✓${NC} Draft created: ${draft_id} [${category}]"
  }

  # Process grouped items
  local group_count
  group_count=$(echo "$json_block" | jq '.groups | length' 2>/dev/null || echo 0)
  local i=0
  while [[ $i -lt $group_count ]]; do
    local draft_id draft_content category label maps_to
    draft_id=$(echo "$json_block" | jq -r ".groups[$i].draft_id")
    draft_content=$(echo "$json_block" | jq -r ".groups[$i].draft_content")
    category=$(echo "$json_block" | jq -r ".groups[$i].category")
    label=$(echo "$json_block" | jq -r ".groups[$i].label")
    maps_to=$(echo "$json_block" | jq -r ".groups[$i].maps_to")

    if [[ -n "$draft_id" && "$draft_id" != "null" ]]; then
      _promote_or_scope_defer "$draft_id" "$draft_content" "$category" "$label" "$maps_to"
    fi
    i=$((i + 1))
  done

  # Process standalone items
  local standalone_count
  standalone_count=$(echo "$json_block" | jq '.standalone | length' 2>/dev/null || echo 0)
  i=0
  while [[ $i -lt $standalone_count ]]; do
    local draft_id draft_content category label maps_to
    draft_id=$(echo "$json_block" | jq -r ".standalone[$i].draft_id")
    draft_content=$(echo "$json_block" | jq -r ".standalone[$i].draft_content")
    category=$(echo "$json_block" | jq -r ".standalone[$i].category")
    label=$(echo "$json_block" | jq -r ".standalone[$i].label // .standalone[$i].draft_id")
    maps_to=$(echo "$json_block" | jq -r ".standalone[$i].maps_to")

    if [[ -n "$draft_id" && "$draft_id" != "null" ]]; then
      _promote_or_scope_defer "$draft_id" "$draft_content" "$category" "$label" "$maps_to"
    fi
    i=$((i + 1))
  done

  # --- Create scope-deferred file (if any JM_NEW items were intercepted) ---
  local scope_deferred_count=${#scope_deferred_ids[@]}
  if [[ $scope_deferred_count -gt 0 ]]; then
    {
      echo "# Scope-Deferred Items from: ${safe_name}"
      echo "> These items were classified as JM_NEW but deferred because active JM execution"
      echo "> is in progress. Promote to draft with: kh promote \"id\""
      echo ""
      for entry in "${scope_deferred_entries[@]}"; do
        local sd_id sd_label sd_maps sd_content
        sd_id=$(echo "$entry" | cut -f1)
        sd_label=$(echo "$entry" | cut -f2)
        sd_maps=$(echo "$entry" | cut -f3)
        sd_content=$(echo "$entry" | cut -f4-)
        echo "## ${sd_label}"
        echo "- **ID:** ${sd_id}"
        echo "- **Category:** JM_NEW"
        echo "- **Maps to:** ${sd_maps}"
        echo ""
        echo "### Stored Draft Content"
        echo '```'
        echo "${sd_content}"
        echo '```'
        echo ""
      done
    } > "${RAW_DIR}/${safe_name}_deferred_scope.md"
    echo -e "  ${CYAN}⟲${NC} Scope-deferred: ${scope_deferred_count} items → raw/${safe_name}_deferred_scope.md"
  fi

  # --- Create deferred file ---
  local deferred_count
  deferred_count=$(echo "$json_block" | jq '.deferred | length' 2>/dev/null || echo 0)
  if [[ $deferred_count -gt 0 ]]; then
    {
      echo "# Deferred Items from: ${safe_name}"
      echo "> These items are valid but not current scope. Create a new raw input if they become relevant."
      echo ""
      echo "$json_block" | jq -r '.deferred[] | "## \(.title)\n- **Category:** \(.category)\n- **Reasoning:** \(.reasoning)\n"'
    } > "${RAW_DIR}/${safe_name}_deferred.md"
    echo -e "  ${YELLOW}⟲${NC} Deferred: ${deferred_count} items → raw/${safe_name}_deferred.md"
  fi

  # --- Create rejected file ---
  local rejected_count
  rejected_count=$(echo "$json_block" | jq '.rejected | length' 2>/dev/null || echo 0)
  if [[ $rejected_count -gt 0 ]]; then
    {
      echo "# Rejected Items from: ${safe_name}"
      echo "> These items need human review — they were too vague or not implementation tasks."
      echo ""
      echo "$json_block" | jq -r '.rejected[] | "## \(.title)\n- **Category:** \(.category)\n- **Reasoning:** \(.reasoning)\n"'
    } > "${RAW_DIR}/${safe_name}_rejected.md"
    echo -e "  ${RED}✗${NC} Rejected: ${rejected_count} items → raw/${safe_name}_rejected.md"
  fi

  # --- Update JM/UF catalogs with [PLANNED] entries ---
  local uf_file=""
  for uf_path in "${PROJECT_ROOT}/docs/USER_FLOWS.md" "${PROJECT_ROOT}/USER_FLOWS.md"; do
    if [[ -f "$uf_path" ]]; then
      uf_file="$uf_path"
      break
    fi
  done

  local jm_file=""
  for jm_path in "${PROJECT_ROOT}/docs/JOURNEY_MAPPINGS.md" "${DOCS_PATH}/JOURNEY_MAPPINGS.md"; do
    if [[ -f "$jm_path" ]]; then
      jm_file="$jm_path"
      break
    fi
  done

  local catalog_updates=0

  # Append [PLANNED] entries for JM_NEW_UF items to USER_FLOWS.md
  if [[ -n "$uf_file" ]]; then
    local all_items
    all_items=$(echo "$json_block" | jq -r '
      [(.groups[]? | {draft_id, category, maps_to, label}),
       (.standalone[]? | {draft_id, category, maps_to, label: .draft_id})]
      | .[] | select(.category == "JM_NEW_UF" or .category == "DEFERRED_PROMOTED")
      | "\(.draft_id)|\(.maps_to)|\(.label)"
    ' 2>/dev/null || true)

    if [[ -n "$all_items" ]]; then
      echo "" >> "$uf_file"
      echo "<!-- [PLANNED] entries added by kh breakdown on ${timestamp} from raw/${safe_name} -->" >> "$uf_file"
      while IFS='|' read -r uf_id uf_maps uf_label; do
        if [[ -n "$uf_id" ]]; then
          # Only add if not already in the file
          if ! grep -q "flow-${uf_id}" "$uf_file" 2>/dev/null; then
            {
              echo ""
              echo "### ${uf_label}"
              echo "- **ID:** flow-${uf_id}"
              echo "- **Lifecycle:** NEW"
              echo "- **Description:** [PLANNED] — Identified during breakdown. Maps to: ${uf_maps}"
              echo "- **Steps:** (defined during grooming)"
              echo "- **Serves tasks:** ${uf_id}"
              echo "- **Verification:** TBD"
              echo "- **Test file:** none"
              echo "- **Status:** PLANNED"
            } >> "$uf_file"
            catalog_updates=$((catalog_updates + 1))
          fi
        fi
      done <<< "$all_items"
    fi
  fi

  # Append [PLANNED] entries for JM_NEW items to JOURNEY_MAPPINGS.md index
  if [[ -n "$jm_file" ]]; then
    local new_jms
    new_jms=$(echo "$json_block" | jq -r '
      [(.groups[]? | {draft_id, category, label}),
       (.standalone[]? | {draft_id, category, label: .draft_id})]
      | .[] | select(.category == "JM_NEW")
      | "\(.draft_id)|\(.label)"
    ' 2>/dev/null || true)

    if [[ -n "$new_jms" ]]; then
      echo "" >> "$jm_file"
      echo "<!-- [PLANNED] journeys added by kh breakdown on ${timestamp} from raw/${safe_name} -->" >> "$jm_file"
      while IFS='|' read -r jm_id jm_label; do
        if [[ -n "$jm_id" ]]; then
          if ! grep -q "$jm_id" "$jm_file" 2>/dev/null; then
            {
              echo ""
              echo "## JOURNEY: ${jm_label} [PLANNED]"
              echo ""
              echo "| ID | Name | Status |"
              echo "|----|------|--------|"
              echo "| ${jm_id} | ${jm_label} | PLANNED — identified during breakdown from raw/${safe_name} |"
              echo ""
              echo "> Steps to be defined during grooming."
            } >> "$jm_file"
            catalog_updates=$((catalog_updates + 1))
          fi
        fi
      done <<< "$new_jms"
    fi
  fi

  if [[ $catalog_updates -gt 0 ]]; then
    echo -e "  ${CYAN}📘${NC} Updated catalogs: ${catalog_updates} [PLANNED] entries added"
    log "INFO" "Added ${catalog_updates} [PLANNED] entries to JM/UF catalogs"
  fi

  # --- Update raw_items state ---
  local temp_file; temp_file=$(mktemp)
  local promoted_json
  if [[ ${#promoted_ids[@]} -gt 0 ]]; then
    promoted_json=$(printf '%s\n' "${promoted_ids[@]}" | jq -R . | jq -s .)
  else
    promoted_json='[]'
  fi
  jq --arg id "$safe_name" --arg ts "$timestamp" --argjson promoted "$promoted_json" \
     --arg bfile "raw/${safe_name}_breakdown.md" \
     --argjson deferred "$deferred_count" --argjson rejected "$rejected_count" \
     --argjson scope_deferred "$scope_deferred_count" \
     '(.raw_items[] | select(.id == $id)) |= (
       .status = "broken_down" |
       .breakdown_file = $bfile |
       .promoted_drafts = $promoted |
       .deferred_count = $deferred |
       .deferred_scope_count = $scope_deferred |
       .rejected_count = $rejected |
       .breakdown_at = $ts
     ) | .last_updated = $ts' \
     "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"

  # --- Summary ---
  echo ""
  local total_promoted=${#promoted_ids[@]}
  local summary_json
  summary_json=$(echo "$json_block" | jq -r '.summary // {}')
  local redundant_count
  redundant_count=$(echo "$summary_json" | jq -r '.redundant // 0')

  header
  echo -e "  ${GREEN}Breakdown complete: ${safe_name}${NC}"
  echo -e "  Promoted to draft: ${GREEN}${total_promoted}${NC}"
  [[ $scope_deferred_count -gt 0 ]] && echo -e "  Scope-deferred:    ${CYAN}${scope_deferred_count}${NC} (JM_NEW → active scope)"
  [[ $deferred_count -gt 0 ]] && echo -e "  Deferred:          ${YELLOW}${deferred_count}${NC}"
  [[ $rejected_count -gt 0 ]] && echo -e "  Rejected:          ${RED}${rejected_count}${NC}"
  [[ "$redundant_count" -gt 0 ]] && echo -e "  Redundant:         ${CYAN}${redundant_count}${NC}"
  echo ""
  echo -e "  Report: ${BLUE}raw/${safe_name}_breakdown.md${NC}"
  echo -e "  Next:   ${BLUE}kh status${NC} to see promoted drafts"
  header
}

# ═══════════════════════════════════════════════════════════
# MAIN DISPATCH
# ═══════════════════════════════════════════════════════════

main() {
  case "${1:-}" in
    init)
      cmd_init ;;
    raw)
      load_config; cmd_raw "${2:-}" "${3:-}" ;;
    breakdown)
      [[ -z "${2:-}" ]] && { echo "Usage: kh breakdown \"name\" [--dry-run]"; exit 1; }
      load_config; cmd_breakdown "$2" "${3:-}" ;;
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
    close)
      cmd_close "${2:-}" ;;
    help|--help|-h)
      echo ""
      echo -e "${BLUE}ThousandHand (KH)${NC} - Claude Workflow Orchestration"
      echo ""
      echo "Usage: kh <command>"
      echo ""
      echo -e "${YELLOW}Pre-flow (brain dump → discrete items):${NC}"
      echo "  raw \"name\"              Add raw brain dump from stdin (pipe or heredoc)"
      echo "  raw list                List all raw inputs + breakdown status"
      echo "  raw show \"name\"         Show raw input + breakdown report"
      echo "  breakdown \"name\"        AI triage: split raw into drafts (auto-promotes)"
      echo "  breakdown \"name\" --dry-run  Preview breakdown without creating files"
      echo ""
      echo -e "${YELLOW}Setup:${NC}"
      echo "  init                    Initialize .kh structure + user flows + architecture doc"
      echo "  add \"name\"              Add discrete draft from stdin (skip pre-flow)"
      echo "  status                  Show queue status + user flow coverage + active phase"
      echo "  view \"name\"             View task file + metadata"
      echo "  prioritize \"name\" <n>   Set priority (lower = processed first)"
      echo ""
      echo -e "${YELLOW}Processing:${NC}"
      echo "  run                     Process all drafts (single session per item)"
      echo "  logs                    Live-tail active session (or show last)"
      echo "  watch                   Continuous monitoring mode"
      echo "  stop                    Graceful halt (from another terminal)"
      echo ""
      echo -e "${YELLOW}Delivery:${NC}"
      echo "  close [modifier]        Closing ceremony — comprehensive review + test gap"
      echo "                          analysis + UAT preparation. Optional modifier for"
      echo "                          versioning (e.g., kh close v3, kh close sprint-1)"
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
      echo "  raw | breakdown                          (pre-flow)"
      echo "  init | add | status | view | prioritize  (setup)"
      echo "  run | logs | watch | stop                (processing)"
      echo "  close [modifier]                         (delivery)"
      echo "  demote | promote | resume | remove       (management)"
      echo ""
      echo "Run 'kh help' for details."
      echo ""
      ;;
  esac
}

main "$@"
