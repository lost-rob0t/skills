---
name: free-resources
description: memory, cpu, resources, kill, consent, cleanup
compatibility: Linux with procfs; stopping other users' processes requires root, which this skill never requests.
---

# Free system resources with consent

## Goal

Reclaim CPU, memory, or I/O by stopping resource-heavy processes - only with
explicit per-process user approval, never by pattern or guesswork.

## Input

- a Linux machine whose `/proc` is readable;
- a debug verdict (ideally from the `debug-system` skill) naming the resource
  under pressure.

## Output

A ranked hog list, the user's approved PID set, the signal result per PID, and
before/after resource numbers. Exit status: `0` all targets stopped, `1`
something survived or was refused, `2` unusable environment.

## Workflow

1. Rank the suspects (read-only; `--sort cpu|mem|io` to match the verdict):

   ```sh
   python3 skills/free-resources/scripts/hogs.py list --sort mem
   ```

   `KIND` marks `critical` (session-critical, never a target), `agent`
   (stopping it kills a live agent session), and `normal`.

2. Present the list to the user and ask which PIDs to stop. Every PID needs an
   explicit user decision. For `agent` kind, say out loud that killing it ends
   a live session. If the user is not reachable, stop and report instead of
   acting.

3. After approval, signal gracefully first and verify:

   ```sh
   python3 skills/free-resources/scripts/hogs.py kill --pid PID1 --pid PID2 --yes
   ```

   `SIGKILL` (`--signal KILL`) only after a TERM attempt survived its timeout
   and the user re-approves that specific PID.

4. Confirm the effect with fresh evidence: re-run the ranking or the
   `debug-system` diagnostic and report freed memory/IO before declaring done.

## Rules

- Consent is per PID, per action. A list approval from earlier does not cover a
  new kill; re-check that each PID still runs the same comm before signaling.
- Never signal: PID 1, this agent's own process group, `critical` kind
  processes, or processes owned by other users (root escalation is out of
  scope for this skill).
- The script refuses unapproved, critical, foreign, and vanished PIDs; do not
  work around a refusal with raw `kill`, `pkill`, or `xkill`.
- Prefer TERM over KILL. If nothing is safe to stop, say so and suggest
  non-destructive options (restart a wedged watcher, close idle sessions).
