#!/usr/bin/env bash
# Pull a remote directory to the local server via rsync over SSH.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  rsync_pull_from_remote.sh [options] <remote_spec> <local_dest>
  rsync_pull_from_remote.sh [options] --config <config_file> [--job <name>]

Arguments:
  remote_spec    user@host:/remote/path/   (remote path trailing / = sync contents)
  local_dest     Local destination directory

Options:
  -u, --user USER          SSH user (overrides remote_spec)
  -H, --host HOST          Remote host (overrides remote_spec)
  -p, --port PORT          SSH port (default: 22)
  -s, --source PATH        Remote source path (alternative to remote_spec)
  -d, --dest PATH          Local destination path (alternative to positional)
  -i, --identity FILE      SSH private key path
  -e, --exclude PATTERN    Exclude pattern (repeatable)
  -n, --dry-run            Preview changes without writing
  -D, --delete             Delete local files not present on remote (use with care)
  -q, --quiet              Less output
  -P, --password-auth      Allow password auth (interactive prompt or SSHPASS env)
  -c, --config FILE        Config file with multiple sync jobs
  -j, --job NAME           Run one job from config (default: all jobs)
  -h, --help               Show this help

Password auth:
  Interactive:  rsync_pull_from_remote.sh -P -p 42994 root@host:/src/ /dst/
  Non-interactive (requires sshpass):
    SSHPASS='your_password' rsync_pull_from_remote.sh -P -p 42994 root@host:/src/ /dst/

Examples:
  ./rsync_pull_from_remote.sh -p 42994 root@connect.example.com:/data/ /home/ubuntu/data/
  ./rsync_pull_from_remote.sh -n -p 42994 root@host:/remote/dir/ ./local/dir/
  ./rsync_pull_from_remote.sh -H 10.0.0.5 -u ubuntu -s /opt/app/ -d /home/ubuntu/app/
  ./rsync_pull_from_remote.sh --config rsync_jobs.conf --job my_job
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
  log "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

SSH_USER=""
SSH_HOST=""
SSH_PORT="22"
REMOTE_SRC=""
LOCAL_DEST=""
IDENTITY=""
DRY_RUN=0
DELETE=0
QUIET=0
PASSWORD_AUTH=0
CONFIG_FILE=""
JOB_NAME=""
declare -a EXCLUDES=()

parse_host_spec() {
  local spec="$1"
  [[ "$spec" == *:* ]] || die "Remote spec must look like user@host:/path/ or host:/path/"

  local host_part="${spec%%:*}"
  REMOTE_SRC="${spec#*:}"

  if [[ "$host_part" == *@* ]]; then
    SSH_USER="${host_part%%@*}"
    SSH_HOST="${host_part#*@}"
  else
    SSH_HOST="$host_part"
  fi
}

build_ssh_command() {
  local -a ssh_opts=(
    -p "$SSH_PORT"
    -o StrictHostKeyChecking=accept-new
  )
  local cmd="ssh"
  local opt

  if [[ "$PASSWORD_AUTH" -eq 0 && -z "${SSHPASS:-}" ]]; then
    ssh_opts+=(-o BatchMode=yes)
  fi

  if [[ -n "$IDENTITY" ]]; then
    ssh_opts+=(-i "$IDENTITY")
  fi

  if [[ -n "${SSHPASS:-}" ]]; then
    require_cmd sshpass
    PASSWORD_AUTH=1
    cmd="sshpass -e ssh"
  fi

  for opt in "${ssh_opts[@]}"; do
    cmd+=" $(printf '%q' "$opt")"
  done
  printf '%s' "$cmd"
}

run_rsync() {
  local remote_src="$1"
  local local_dest="$2"

  [[ -n "$SSH_HOST" ]] || die "Remote host is required"
  [[ -n "$remote_src" ]] || die "Remote source path is required"
  [[ -n "$local_dest" ]] || die "Local destination path is required"

  if [[ -z "$SSH_USER" ]]; then
    SSH_USER="${USER:-ubuntu}"
  fi

  mkdir -p "$local_dest"

  local -a rsync_opts=(
    -a
    -z
    --partial
    --human-readable
    --info=progress2
  )

  if [[ "$DRY_RUN" -eq 1 ]]; then
    rsync_opts+=(--dry-run)
  fi
  if [[ "$DELETE" -eq 1 ]]; then
    rsync_opts+=(--delete)
  fi
  if [[ "$QUIET" -eq 1 ]]; then
    rsync_opts=(-a -z --partial)
  fi

  local -a exclude_opts=()
  for pattern in "${EXCLUDES[@]}"; do
    exclude_opts+=(--exclude "$pattern")
  done

  local remote="${SSH_USER}@${SSH_HOST}:${remote_src}"
  local ssh_cmd
  ssh_cmd="$(build_ssh_command)"

  log "Syncing ${remote} -> ${local_dest} (port ${SSH_PORT})"
  [[ "$DRY_RUN" -eq 1 ]] && log "DRY RUN: no files will be changed"
  [[ "$DELETE" -eq 1 ]] && log "DELETE enabled: extra local files will be removed"

  # shellcheck disable=SC2086
  rsync "${rsync_opts[@]}" \
    "${exclude_opts[@]}" \
    -e "$ssh_cmd" \
    "$remote" \
    "$local_dest"
}

run_job_from_config() {
  local job="$1"
  local in_job=0
  local job_user="" job_host="" job_port="22" job_source="" job_dest=""
  local job_identity="" job_delete="0" job_password_auth="0" job_excludes=""

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue

    if [[ "$line" == "[${job}]" ]]; then
      in_job=1
      continue
    fi
    if [[ "$line" == "["*"]" ]]; then
      in_job=0
      continue
    fi
    [[ "$in_job" -eq 1 ]] || continue

    local key="${line%%=*}"
    local value="${line#*=}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    case "$key" in
      user) job_user="$value" ;;
      host) job_host="$value" ;;
      port) job_port="$value" ;;
      source) job_source="$value" ;;
      dest) job_dest="$value" ;;
      identity) job_identity="$value" ;;
      delete) job_delete="$value" ;;
      password_auth) job_password_auth="$value" ;;
      exclude) job_excludes="${job_excludes}${value}"$'\n' ;;
      *) die "Unknown config key in job [$job]: $key" ;;
    esac
  done < "$CONFIG_FILE"

  [[ -n "$job_host" ]] || die "Job not found in config: $job"

  SSH_USER="$job_user"
  SSH_HOST="$job_host"
  SSH_PORT="$job_port"
  IDENTITY="$job_identity"
  DELETE="$job_delete"
  PASSWORD_AUTH="$job_password_auth"
  EXCLUDES=()
  if [[ -n "$job_excludes" ]]; then
    while IFS= read -r ex; do
      [[ -n "$ex" ]] && EXCLUDES+=("$ex")
    done <<< "$job_excludes"
  fi

  run_rsync "$job_source" "$job_dest"
}

list_jobs_from_config() {
  grep -E '^\[[^]]+\]$' "$CONFIG_FILE" | tr -d '[]'
}

run_config() {
  [[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"

  if [[ -n "$JOB_NAME" ]]; then
    run_job_from_config "$JOB_NAME"
    return
  fi

  while IFS= read -r job; do
    [[ -n "$job" ]] || continue
    log "Running job: $job"
    run_job_from_config "$job"
  done < <(list_jobs_from_config)
}

is_option() {
  case "$1" in
    -u|--user|-H|--host|-p|--port|-s|--source|-d|--dest|-i|--identity|-e|--exclude|-c|--config|-j|--job) return 0 ;;
    -n|--dry-run|-D|--delete|-q|--quiet|-P|--password-auth|-h|--help) return 0 ;;
    --) return 0 ;;
    -*) return 0 ;;
    *) return 1 ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--user) SSH_USER="$2"; shift 2 ;;
    -H|--host) SSH_HOST="$2"; shift 2 ;;
    -p|--port) SSH_PORT="$2"; shift 2 ;;
    -s|--source) REMOTE_SRC="$2"; shift 2 ;;
    -d|--dest) LOCAL_DEST="$2"; shift 2 ;;
    -i|--identity) IDENTITY="$2"; shift 2 ;;
    -e|--exclude) EXCLUDES+=("$2"); shift 2 ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -D|--delete) DELETE=1; shift ;;
    -q|--quiet) QUIET=1; shift ;;
    -P|--password-auth) PASSWORD_AUTH=1; shift ;;
    -c|--config) CONFIG_FILE="$2"; shift 2 ;;
    -j|--job) JOB_NAME="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) die "Unknown option: $1 (use -h for help)" ;;
    *)
      if is_option "$1"; then
        die "Missing value for option: $1"
      fi
      break
      ;;
  esac
done

require_cmd rsync
require_cmd ssh

if [[ -n "$CONFIG_FILE" ]]; then
  run_config
  exit 0
fi

if [[ $# -eq 2 ]]; then
  parse_host_spec "$1"
  LOCAL_DEST="$2"
elif [[ $# -eq 0 && -n "$SSH_HOST" && -n "$REMOTE_SRC" && -n "$LOCAL_DEST" ]]; then
  :
else
  usage
  exit 1
fi

run_rsync "$REMOTE_SRC" "$LOCAL_DEST"
