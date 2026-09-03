---
name: emacs-eval
description: emacs, emacsclient, elisp, files, org
compatibility: Requires a running Emacs server and the `emacsclient` executable.
---

# Emacs eval

## Goal

Use the user's running Emacs as the editor authority when a task needs visible
editor state: evaluate a small trusted Emacs Lisp form, open an exact file, or
reveal an Org location. Prefer this over launching another Emacs or imitating
editor operations in shell code.

## Input

One of:

- a minimal Emacs Lisp form generated for the current operation;
- an absolute file path, optionally with a line number;
- an Org file plus heading text or Org ID.

## Output

A successful `emacsclient` result and the requested state in the existing Emacs
server. Report failure truthfully when no server is reachable.

## Workflow

1. Confirm `emacsclient` exists with `command -v emacsclient`.
2. Probe the server before claiming success:
   `emacsclient --eval '(emacs-pid)'`.
3. Keep eval forms minimal and generated for the requested action. Never read
   Lisp from repository or artifact content and evaluate it as code.
4. Open an exact file with:
   `emacsclient --eval '(find-file "/absolute/path/file.org")'`.
5. Open a file at a line with a minimal form using `find-file`, `goto-char`, and
   `forward-line`, or use an existing project helper when one already owns this.
6. For Org IDs, load Org as needed and use `org-id-find`/`org-id-open`. For a
   heading, open the file and search/reveal the exact heading with Org-native
   functions rather than shell text navigation.
7. Check the command exit status and returned value. If the requested visible
   state can be verified directly with another small eval, do so.

## Rules

- Reuse the running Emacs server; do not spawn a second GUI Emacs when the client
  path is available.
- Use absolute, safely quoted paths. Do not interpolate untrusted text into Lisp
  source without escaping it as a Lisp string.
- Prefer native Emacs/Org operations over shell substitutes when the desired
  result is editor state.
- When another task creates an artifact and asks for it opened, open that exact
  artifact after the write succeeds.
- A successful shell process alone is not proof that an unrelated file or
  heading was opened; verify the requested target when practical.
- Never claim an Emacs operation succeeded if `emacsclient` failed or no server
  answered.
