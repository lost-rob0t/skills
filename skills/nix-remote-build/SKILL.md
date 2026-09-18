---
name: nix-remote-build
description: nix, remote-build, ssh-ng, flakes, copy-back
compatibility: Unix, Nix 2.18+, OpenSSH
---

# Nix Remote Build

## Goal

Force Nix derivations onto a remote builder while keeping realized outputs in
the caller's local Nix store.

## Input

Configure `LLM_WORKER_HOST` and `LLM_WORKER_PROJECT`, or pass `--host` and
`--project`.

## Output

`build` prints realized local store paths after Nix has copied remote outputs
back. `check` preserves `nix flake check` status.

## Workflow

```sh
scripts/nix-remote-build build .#package
scripts/nix-remote-build check
```

The helper sets the remote builder to
`ssh-ng://PROJECT@HOST x86_64-linux - 8 2` and sets local `max-jobs=0`.
That makes local execution a hard failure instead of a fallback.

## Rules

- Do not use local builders in this mode.
- Do not put SSH keys or provider credentials in Nix configuration.
- Verify each reported build output with local `nix path-info`.
- Use a trusted remote Nix daemon identity configured by the worker operator.
- Prefer binary substitutes on both sides before compiling.
