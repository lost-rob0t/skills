---
name: qtile-edit
description: qtile, literate-config, tangle, configuration, tests
compatibility: Requires a Qtile configuration, Python, and Emacs with Org Babel when the configuration is literate.
---

# Edit Qtile safely

## Goal

Change Qtile configuration at its durable source, regenerate owned outputs, and
verify syntax and behavior before reloading the live window manager.

## Workflow

1. Discover the root with `QTILE_CONFIG_ROOT`, defaulting to
   `$HOME/.config/qtile`. Read its local instructions before editing.
2. Classify the target before changing it:
   - `qtile-ai.org` is the canonical source for `config.py`.
   - `qtile-openrouter.org` is the canonical source for `qtile_openrouter.py`.
   - Standalone Python, Elisp, and shell helpers are edited at their own source.
   - Never make a lasting change only in a generated `config.py` or
     `qtile_openrouter.py`.
3. Search the source and nearby tests for the behavior. Preserve existing
   ownership, keybinding, event-loop, and display/server conventions.
4. Edit the canonical source. For an Org source, tangle from that file:

   ```sh
   emacs --batch --quick qtile-ai.org --funcall org-babel-tangle
   emacs --batch --quick qtile-openrouter.org --funcall org-babel-tangle
   ```

   Tangle only the source that changed when possible.
5. Verify generated parity and syntax from the configuration root:

   ```sh
   python -m py_compile config.py qtile_telemetry.py
   qtile check -c config.py
   ```

6. Run the narrowest relevant tests, then the full Qtile suite when practical.
   Tests must check behavior and source/generated parity, not only file
   existence.
7. Invoke `qtile-reload` only after validation passes, then invoke
   `qtile-confirm` for any visual or runtime-facing change.

## Rules

- Keep keybindings documented in their canonical literate source.
- Do not hardcode a monitor, network interface, display, username, or hostname
  when runtime discovery or an existing configuration abstraction is available.
- Do not block Qtile’s event loop with Git, network, or long-running commands.
- Do not overwrite unrelated work in a dirty tree.
- Do not commit or merge unless the user explicitly requests it.
