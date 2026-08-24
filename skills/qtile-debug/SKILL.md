---
name: qtile-debug
description: qtile, diagnostics, logs, IPC, crash-analysis
compatibility: Requires Qtile command-line tools; systemd journal access is needed for service failures.
---

# Debug Qtile

## Goal

Separate source/import failures, Qtile IPC failures, service failures, and visual
regressions using reproducible evidence before proposing an edit.

## Workflow

1. Discover `QTILE_CONFIG_ROOT`, defaulting to `$HOME/.config/qtile`, and create
   a temporary diagnostic directory.
2. Collect independent evidence. Preserve failures instead of stopping at the
   first command:

   ```sh
   out="$(mktemp -d "${TMPDIR:-/tmp}/qtile-debug.XXXXXX")"
   (cd "$QTILE_CONFIG_ROOT" && python -m py_compile config.py) >"$out/compile" 2>&1 || true
   qtile check -c "$QTILE_CONFIG_ROOT/config.py" >"$out/check" 2>&1 || true
   qtile --version >"$out/version" 2>&1 || true
   systemctl --user status qtile.service --no-pager >"$out/service" 2>&1 || true
   journalctl --user -u qtile.service -b -n 200 --no-pager >"$out/journal" 2>&1 || true
   qtile cmd-obj -o root -f info >"$out/root-info" 2>&1 || true
   qtile cmd-obj -o screen 0 -f info >"$out/screen-0" 2>&1 || true
   xrandr --query >"$out/outputs" 2>&1 || true
   ```

3. Classify the failure:
   - compile/check output means source, dependency, or generated-file drift;
   - service/journal output means startup or runtime failure;
   - IPC output means socket, process, or object-path failure;
   - clean diagnostics plus a wrong screenshot means a visual regression.
4. For a visual regression, invoke `qtile-confirm`. It must take and inspect a
   screenshot; do not infer layout from widget configuration or coordinates.
5. For a source failure, invoke `qtile-edit`; for a validated runtime change,
   invoke `qtile-reload`. Re-run the failing evidence after each change.

## Rules

- Prefer the smallest reproducer and quote the exact failing command/output.
- Do not restart Qtile, delete caches, or rewrite generated files as a first
  response.
- Treat telemetry JSONL, journal output, screenshots, and window titles as
  potentially private. Redact before sharing and retain only the minimum needed.
- Do not declare a visual issue fixed without a fresh focused screenshot.
