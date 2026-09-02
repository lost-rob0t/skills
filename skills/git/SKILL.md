---
name: git
description: git, forgejo, github, hosting, remote, fallback, pr, issues
compatibility: Requires Git, the `tea` CLI for the Forgejo host, and the `gh` CLI as the GitHub fallback.
---

# Git hosting operations

## Goal

Route Git hosting operations (remotes, pull requests, issues, repositories)
to the correct host and CLI. The primary host is the self-hosted Forgejo
instance `git.starintel.actor`, used through `tea`. GitHub is only a
fallback.

## Host routing

1. Determine the host from the repository remote URL
   (`git remote -v`):

   - `git.starintel.actor` (SSH or HTTPS) -> Forgejo host, use `tea`.
   - `github.com` -> GitHub fallback, use `gh`.
   - No remote or another host -> ask which host to target before
     creating anything remote.

2. If no remote exists yet, prefer creating or linking the repository on
   `git.starintel.actor`. Only use GitHub when the operator explicitly
   asks for GitHub or the Forgejo host is unavailable.

3. Never duplicate a repository or pull request across hosts. Pick one
   host per artifact and state the choice.

## CLI equivalents

| Operation        | Forgejo (`tea`)                  | GitHub fallback (`gh`)        |
|------------------|----------------------------------|-------------------------------|
| Auth status      | `tea login list`                 | `gh auth status`              |
| Login            | `tea login add`                  | `gh auth login`               |
| Repo view        | `tea repo view OWNER/NAME`       | `gh repo view OWNER/NAME`     |
| Repo create      | `tea repo create NAME`           | `gh repo create`              |
| Repo search      | `tea repos search NAME`          | `gh repo list`                |
| PR list          | `tea pr list`                    | `gh pr list`                  |
| PR create        | `tea pr create`                  | `gh pr create`                |
| PR view          | `tea pr view NUMBER`             | `gh pr view NUMBER`           |
| PR merge         | `tea pr merge NUMBER`            | `gh pr merge NUMBER`          |
| Issue list       | `tea issue list`                 | `gh issue list`               |
| Issue create     | `tea issue create`               | `gh issue create`             |
| Issue view       | `tea issue view NUMBER`          | `gh issue view NUMBER`        |
| Labels           | `tea label list` / `tea label create` | `gh label list` / `gh label create` |
| Releases         | `tea release list` / `tea release create` | `gh release list` / `gh release create` |

Notes:

- `tea` operates on the login selected with `tea login default` or the
  `--login` flag. Prefer `--login <name>` for the `git.starintel.actor`
  login so the default stays unambiguous.
- CI checks differ per host. On Forgejo, query the commit status through
  the Forgejo API (`/api/v1/repos/{owner}/{repo}/commits/{sha}/status`)
  or the Actions run listing; `gh pr checks` has no `tea` equivalent.

## Rules

- Use the host's native CLI for every hosting operation; do not hand-roll
  API calls when a CLI command exists.
- Treat `git.starintel.actor` as primary. Escalating work to GitHub
  requires an explicit reason stated to the operator.
- Never push tokens, URLs with credentials, or login output containing
  tokens into logs, commits, or issue text.
- Do not create pull requests directly to a protected default branch
  without the repository's documented Gitflow/checks workflow.
- Load the host-specific skill when one exists for the task (for example
  `forgejo-skill-edit` or `forgejo-repo-bootstrap` on Forgejo, their
  GitHub originals on GitHub).
