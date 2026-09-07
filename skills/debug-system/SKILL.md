---
name: debug-system
description: debug, cpu, io, memory, pressure, diagnostics, performance
compatibility: Linux with procfs; PSI requires kernel 4.20+; per-process I/O needs readable /proc/<pid>/io.
---

# Debug system performance

## Goal

Identify the dominant bottleneck (CPU, memory/swap, or I/O) from procfs evidence
and recommend a fix, without mutating anything.

## Input

- a Linux machine whose `/proc` is readable (per-process data is best-effort for
  processes owned by other users);
- optional symptom description from the user.

## Output

A verdict naming the bottleneck, the evidence lines behind it, ranked suspect
processes, and concrete next actions. Exit status: `0` healthy, `1` pressure
detected, `2` unusable environment.

## Workflow

1. Run the diagnostic script (2-5s window; longer for intermittent symptoms):

   ```sh
   python3 skills/debug-system/scripts/diagnose.py --interval 3
   ```

   Use `--json` when feeding another tool; the exit status classifies health.

2. Interpret the verdict. Trust PSI averages plus measured rates over single
   snapshots: `some` means work was stalled, `full` means everything stalled.
   Swap that is merely allocated is fine; swap moving at MiB/s is thrashing.

3. Collect corroborating evidence the script cannot see:

   ```sh
   journalctl -k -b --no-pager | grep -iE "oom|out of memory" | tail
   dmesg --level=err,warn --notime | tail
   ```

4. Name the fix class before touching anything:
   - spin loop (high CPU, no output): restart the wedged process, as with any
     service; killing data first, consent always;
   - memory/swap: stop RSS+swap hogs via the `free-resources` skill;
   - I/O: find the writer; a flush storm means a process, not a failing disk;
   - recurring OOM: cap or restart the offender; do not silently add swap.

5. Re-run the script after any change and compare verdicts. One change per
   measurement.

## Rules

- Diagnose read-only. Never write to `/proc/sys`, `sysctl`, cgroups, or kill a
  process as part of debugging; stopping processes belongs to `free-resources`.
- Quote the evidence lines that justify the verdict; do not guess between
  categories when scores are close - say they are close.
- Treat process command lines and titles as potentially private; redact before
  sharing outside the machine.
- Per-process I/O and memory of other users' processes may be unreadable;
  report coverage gaps instead of presenting partial ranks as complete.
