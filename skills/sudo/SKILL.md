---
name: sudo
description: sudo, privilege-escalation, desktop-portals, xdg-desktop-portal, polkit, authentication
---

# Desktop-authenticated privilege

## Goal

Run an explicitly authorized Linux command with elevated privileges while keeping authentication in the user's desktop session.

## Input

- the exact command, arguments, and target paths;
- an active desktop session with an available XDG Desktop Portal broker and registered polkit authentication agent;
- the `pkexec` privilege helper.

## Output

Return the command's exit status and observable result. Never return, store, or log a password, token, or authentication response.

## Workflow

1. Resolve the requested executable and arguments. Separate compound shell syntax, review the target, and reduce the operation to the least privilege needed.
2. Treat `sudo` as a request for elevated privilege, not permission to collect credentials. State the exact command and expected effect before a state-changing operation.
3. Run this skill's read-only `scripts/probe.py --json` helper. It checks `pkexec`, desktop display state, and the common XDG Desktop Portal broker without requesting elevation or collecting credentials. If the probe is not ready, stop. The probe intentionally does not claim it can generically prove a registered polkit agent.
4. When the operation is not already exposed by a polkit-aware service, invoke the resolved `pkexec` with `--disable-internal-agent` and the exact executable plus arguments. This requires the session's graphical polkit agent and prevents a textual password fallback.
5. If the user specifically requires `sudo` semantics, use `sudo -n` only when an existing authorization can satisfy the command without prompting. Otherwise stop and ask the user to perform it locally; never use `sudo -S`, `SUDO_ASKPASS`, shell-embedded passwords, or password files.
6. Verify the result without privilege when possible. Check ownership, permissions, and generated state so a root-owned artifact is not mistaken for a complete operation.

## Rules

- XDG Desktop Portal does not define a generic sudo or privilege-authentication portal. The probe only confirms that the common portal broker is reachable; polkit still performs privilege authorization. Do not invent a portal name or treat the Secret portal as an authorization mechanism.
- Use a concrete portal-backed helper only when the current runtime exposes and documents that interface; keep its authentication UI and response outside the agent's credential handling.
- Never run an unreviewed `pkexec` shell, interpreter, pipeline, wildcard expansion, or concatenated command string. Prefer an absolute executable and an argument vector.
- If no desktop polkit agent is available, authentication is dismissed, or authorization is denied, fail closed and report that state separately from command failure.
- Do not change polkit rules, sudoers, PAM, or desktop-session configuration unless the user separately requests that configuration change.
