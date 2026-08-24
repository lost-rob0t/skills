# Impeccable upstream provenance

This skill is an integration of the external **Impeccable** project. It is not original work created by `lost-rob0t/skills` or by the maintainer of this repository.

- Upstream project: https://github.com/pbakaus/impeccable
- Upstream author/maintainer attribution: Paul Bakaus (`pbakaus`) and Impeccable contributors
- License: Apache-2.0
- Imported version: 4.1.1
- Pinned upstream revision reviewed for this integration: `c3a30086bc395ea2197fbe287dc59c18969aaeb6`
- Upstream homepage: https://impeccable.style

## Upstream behavior

Impeccable provides one design skill with commands including `init`, `shape`, `critique`, `audit`, `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize`, and `live`.

The maintained upstream CLI is the installation authority:

```sh
npx impeccable install
npx impeccable update
```

For deterministic project setup, detect the current harness and pass it explicitly:

```sh
npx impeccable install --providers=<provider> --scope=project
```

Upstream currently documents provider support including Claude Code, Cursor, Gemini CLI, Codex CLI, GitHub Copilot, Grok Build, OpenCode, Pi, Qoder, Trae, Rovo Dev, Mistral Vibe, and Google Antigravity. Provider support changes upstream; verify the current upstream documentation before adding a new repository adapter or promising compatibility.

## Refreshing this integration

1. Review the current upstream `README.md`, generic Agent Skills package, license, and release/version metadata.
2. Update the version and revision recorded here and in `SKILL.md`.
3. Preserve the upstream author, source URL, and license metadata.
4. Do not claim this repository authored Impeccable.
5. Prefer the maintained upstream CLI for generated provider-specific files instead of vendoring those generated trees here.
