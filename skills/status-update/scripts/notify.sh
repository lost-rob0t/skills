#!/usr/bin/env bash
# Send a desktop status notification via dunst (dunstify) with libnotify
# (notify-send) as the backup backend. Fails closed when no backend exists.
set -euo pipefail

usage() {
  printf '%s\n' \
    'usage: notify.sh --title TITLE [--message BODY] [--urgency low|normal|critical]' \
    '                 [--timeout MS] [--app-name NAME] [--dry-run] [--resolve]' \
    '' \
    'options:' \
    '  --title TITLE      notification summary (required)' \
    '  --message BODY     optional notification body' \
    '  --urgency LEVEL    low, normal, or critical (default: normal)' \
    '  --timeout MS       display duration in milliseconds (default: 10000)' \
    '  --app-name NAME    sender name shown by the daemon (default: agent)' \
    '  --dry-run          print the command that would run; send nothing' \
    '  --resolve          print the selected backend name only, then exit' \
    '  -h, --help         show this help' \
    '' \
    'backend order: dunstify (dunst), then notify-send (libnotify). If the first' \
    'backend fails to send, the other one is tried once.'
}

title=""
message=""
urgency="normal"
timeout="10000"
app_name="agent"
mode="send"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --title)    [ "$#" -ge 2 ] || { echo "notify: --title needs a value" >&2; exit 2; }
                title="$2"; shift 2 ;;
    --message)  [ "$#" -ge 2 ] || { echo "notify: --message needs a value" >&2; exit 2; }
                message="$2"; shift 2 ;;
    --urgency)  [ "$#" -ge 2 ] || { echo "notify: --urgency needs a value" >&2; exit 2; }
                urgency="$2"; shift 2 ;;
    --timeout)  [ "$#" -ge 2 ] || { echo "notify: --timeout needs a value" >&2; exit 2; }
                timeout="$2"; shift 2 ;;
    --app-name) [ "$#" -ge 2 ] || { echo "notify: --app-name needs a value" >&2; exit 2; }
                app_name="$2"; shift 2 ;;
    --dry-run)  mode="dry-run"; shift ;;
    --resolve)  mode="resolve"; shift ;;
    -h|--help)  usage; exit 0 ;;
    *)          echo "notify: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$urgency" in
  low|normal|critical) ;;
  *) echo "notify: invalid --urgency: $urgency (expected low|normal|critical)" >&2; exit 2 ;;
esac

case "$timeout" in
  ''|*[!0-9]*) echo "notify: invalid --timeout: $timeout (expected milliseconds)" >&2; exit 2 ;;
esac

if [ "$mode" != "resolve" ] && [ -z "$title" ]; then
  echo "notify: --title is required" >&2
  usage >&2
  exit 2
fi

have() { command -v "$1" >/dev/null 2>&1; }

dunstify_path=""
notify_send_path=""
if have dunstify; then
  dunstify_path="$(command -v dunstify)"
fi
if have notify-send; then
  notify_send_path="$(command -v notify-send)"
fi

if [ -z "$dunstify_path" ] && [ -z "$notify_send_path" ]; then
  echo "notify: no notification backend found (need dunstify or notify-send)" >&2
  if [ "$mode" = "resolve" ]; then
    echo "none"
  fi
  exit 1
fi

send_args=(-u "$urgency" -t "$timeout" -a "$app_name" "$title")
if [ -n "$message" ]; then
  send_args+=("$message")
fi

quoted() {
  local out=""
  local arg
  for arg in "$@"; do
    out+=" $(printf '%q' "$arg")"
  done
  printf '%s' "${out# }"
}

run_backend() {
  local backend="$1"
  shift
  if [ "$mode" = "dry-run" ]; then
    printf '%s %s\n' "${backend##*/}" "$(quoted "$@")"
    return 0
  fi
  "$backend" "$@"
}

selected="$dunstify_path"
backup="$notify_send_path"
if [ "$mode" = "resolve" ]; then
  if [ -n "$selected" ]; then
    echo "dunstify"
  else
    echo "notify-send"
  fi
  exit 0
fi

if [ -n "$selected" ]; then
  if run_backend "$selected" "${send_args[@]}"; then
    exit 0
  fi
  echo "notify: backend dunstify failed; trying libnotify backup" >&2
fi

if [ -n "$backup" ]; then
  if run_backend "$backup" "${send_args[@]}"; then
    exit 0
  fi
  echo "notify: backend notify-send failed" >&2
  exit 1
fi

exit 1
