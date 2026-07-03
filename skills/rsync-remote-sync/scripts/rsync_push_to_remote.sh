#!/usr/bin/env bash
# Push a local file or directory to a remote server via rsync over SSH.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  rsync_push_to_remote.sh [options] <local_src> <remote_spec>

Arguments:
  local_src      Local file or directory to upload
  remote_spec    user@host:/remote/path/   (remote path trailing / = copy into dir)

Options:
  -u, --user USER          SSH user (overrides remote_spec)
  -H, --host HOST          Remote host (overrides remote_spec)
  -p, --port PORT          SSH port (default: 22)
  -s, --source PATH        Local source path (alternative to positional)
  -d, --dest PATH          Remote destination path (alternative to remote_spec path)
  -i, --identity FILE      SSH private key path
  -e, --exclude PATTERN    Exclude pattern (repeatable)
  -n, --dry-run            Preview changes without writing
  -D, --delete             Delete remote files not present locally (use with care)
  -q, --quiet              Less output
  -P, --password-auth      Allow password auth (interactive prompt or SSHPASS env)
  -h, --help               Show this help

Password auth:
  Interactive:
    rsync_push_to_remote.sh -P -p 42994 ./local/file root@host:/remote/file

  Non-interactive (requires sshpass):
    SSHPASS='your_password' rsync_push_to_remote.sh -P -p 42994 ./local/ root@host:/remote/

Examples:
  ./rsync_push_to_remote.sh -p 22 ./model.pt user@remote.host:/models/model.pt
  ./rsync_push_to_remote.sh -n -P -p 42994 ./data/ root@host:/root/data/
  ./rsync_push_to_remote.sh -H 10.0.0.5 -u ubuntu -s ./app/ -d /opt/app/
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
LOCAL_SRC=""
REMOTE_DEST=""
IDENTITY=""
DRY_RUN=0
DELETE=0
QUIET=0
PASSWORD_AUTH=0
declare -a EXCLUDES=()

parse_remote_spec() {
  local spec="$1"
  [[ "$spec" == *:* ]] || die "Remote spec must look like user@host:/path/ or host:/path/"

  local host_part="${spec%%:*}"
  REMOTE_DEST="${spec#*:}"

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
  local local_src="$1"
  local remote_dest="$2"

  [[ -n "$SSH_HOST" ]] || die "Remote host is required"
  [[ -n "$local_src" ]] || die "Local source path is required"
  [[ -n "$remote_dest" ]] || die "Remote destination path is required"
  [[ -e "$local_src" ]] || die "Local source does not exist: $local_src"

  if [[ -z "$SSH_USER" ]]; then
    SSH_USER="${USER:-ubuntu}"
  fi

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

  local remote="${SSH_USER}@${SSH_HOST}:${remote_dest}"
  local ssh_cmd
  ssh_cmd="$(build_ssh_command)"

  log "Syncing ${local_src} -> ${remote} (port ${SSH_PORT})"
  [[ "$DRY_RUN" -eq 1 ]] && log "DRY RUN: no files will be changed"
  [[ "$DELETE" -eq 1 ]] && log "DELETE enabled: extra remote files will be removed"

  rsync "${rsync_opts[@]}" \
    "${exclude_opts[@]}" \
    -e "$ssh_cmd" \
    "$local_src" \
    "$remote"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -u|--user) SSH_USER="$2"; shift 2 ;;
    -H|--host) SSH_HOST="$2"; shift 2 ;;
    -p|--port) SSH_PORT="$2"; shift 2 ;;
    -s|--source) LOCAL_SRC="$2"; shift 2 ;;
    -d|--dest) REMOTE_DEST="$2"; shift 2 ;;
    -i|--identity) IDENTITY="$2"; shift 2 ;;
    -e|--exclude) EXCLUDES+=("$2"); shift 2 ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -D|--delete) DELETE=1; shift ;;
    -q|--quiet) QUIET=1; shift ;;
    -P|--password-auth) PASSWORD_AUTH=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) die "Unknown option: $1 (use -h for help)" ;;
    *) break ;;
  esac
done

require_cmd rsync
require_cmd ssh

if [[ $# -eq 2 ]]; then
  LOCAL_SRC="$1"
  parse_remote_spec "$2"
elif [[ $# -eq 0 && -n "$SSH_HOST" && -n "$LOCAL_SRC" && -n "$REMOTE_DEST" ]]; then
  :
else
  usage
  exit 1
fi

run_rsync "$LOCAL_SRC" "$REMOTE_DEST"
