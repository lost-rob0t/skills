---
name: qtile-reload
description: qtile, reload, IPC, validation, runtime-verification
compatibility: Requires a running Qtile session with its command socket available.
---

# Reload Qtile safely

## Goal

Apply a validated Qtile configuration through Qtile’s IPC socket and verify
that the running session remains healthy.

## Workflow

1. Discover `QTILE_CONFIG_ROOT`, defaulting to `$HOME/.config/qtile`, and run the
   configuration check before touching the live session:

   ```sh
   qtile check -c "$QTILE_CONFIG_ROOT/config.py"
   ```

2. Confirm that the user service is active when systemd owns the session:

   ```sh
   systemctl --user is-active qtile.service
   ```

3. Reload through Qtile IPC:

   ```sh
   qtile cmd-obj -o root -f reload_config
   ```

   `systemctl --user reload qtile.service` is not the equivalent operation
   unless the service explicitly defines an `ExecReload`; prefer Qtile IPC.
4. Wait briefly for the configuration to settle, then verify IPC and the
   affected object:

   ```sh
   qtile cmd-obj -o root -f info
   qtile cmd-obj -o screen 0 -f info
   ```

5. Invoke `qtile-confirm` for changes involving geometry, widgets, colors,
   popups, monitor placement, or visibility. A successful IPC response is not
   visual verification.

## Failure handling

- If `qtile check` fails, do not reload. Invoke `qtile-debug` and fix the
  canonical source through `qtile-edit`.
- If IPC fails after a successful check, capture the service journal before
  restarting anything:

  ```sh
  journalctl --user -u qtile.service -b -n 200 --no-pager
  ```

- Do not use a systemd restart as an automatic fallback; it can disrupt the
  session and may hide an IPC or runtime failure.
