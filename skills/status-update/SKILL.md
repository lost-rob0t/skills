---
name: status-update
description: notify-send, dunst, libnotify, desktop-notifications, status, task-completion
---

# Desktop status update

## Goal

Surface a short status notification on the user's desktop after major work or
task completion, so the user can step away while the agent works.

## Input

- a one-line summary (required) and optional longer body describing what
  finished, changed, failed, or needs attention;
- optional urgency (`low`, `normal`, `critical`) matching the outcome.

## Output

A delivered desktop notification, or an explicit report that delivery failed.
The script never blocks task completion and never puts credentials, tokens, or
private hostnames in notification text.

## Workflow

1. Trigger: after completing major work, finishing a task, or reaching a
   decision gate that needs user input, always send a status update with this
   skill before reporting back in chat. Do this even when the outcome is a
   failure.
2. Run this skill's `scripts/notify.sh` helper from the skill base directory:

   ```sh
   scripts/notify.sh --title "Task complete" \
     --message "PR #42 opened; all checks green" --urgency normal
   ```

   Use `--urgency critical` only for outcomes the user must act on now.
3. The script resolves the backend for you: `dunstify` against the running
   dunst daemon first, then `notify-send` (libnotify) against any other
   freedesktop notification daemon as backup. Do not bypass it with ad-hoc
   `notify-send` calls.
4. Verify the script's exit status. On failure, report the delivery failure in
   your final message instead of retrying silently or failing the completed
   work.

## Rules

- Requires a desktop session with a reachable notification daemon (dunst
  primary) plus `dunstify` or `notify-send` (libnotify). Without one, the
  script fails closed; say so and move on.
- Headless, cron, or CI contexts have no notification daemon: expect failure
  and report status in the channel you are working in instead.
- Agent Zero runtimes must not use this desktop path: that runtime is
  instructed to deliver status updates through its ntfy plugin instead. This
  skill ships no ntfy script.
- Keep the summary under about 60 characters; keep sensitive values out of the
  body.
- Never mutate notification daemon configuration from this skill.
