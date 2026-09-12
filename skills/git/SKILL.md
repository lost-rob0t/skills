---
name: git
description: git, github, hosting, remote, pull-request, issues, actions
compatibility: Requires Git and the `gh` CLI authenticated to GitHub.
---

# GitHub hosting operations

## Goal

Use GitHub as the only remote hosting control plane for repository, pull-request,
issue, release, and Actions operations.

## Host policy

1. Inspect repository remotes with `git remote -v` before remote operations.
2. `github.com` is the supported hosting target.
3. If the current remote points at Forgejo, `git.starintel.actor`, or another host,
   do not use that host for Agent Zero work. Resolve or add the corresponding
   GitHub remote/repository instead.
4. Never mirror, duplicate, or create a second PR/issue on another forge as part
   of the same task.
5. If no GitHub repository exists and remote creation is authorized, create it on
   GitHub with `gh repo create`.

## GitHub CLI

| Operation | Command |
|---|---|
| Auth status | `gh auth status` |
| Login | `gh auth login` |
| Repo view | `gh repo view OWNER/NAME` |
| Repo create | `gh repo create` |
| Repo list/search | `gh repo list` / `gh search repos` |
| PR list | `gh pr list` |
| PR create | `gh pr create` |
| PR view | `gh pr view NUMBER` |
| PR checks | `gh pr checks NUMBER` |
| PR merge | `gh pr merge NUMBER` |
| Issue list | `gh issue list` |
| Issue create | `gh issue create` |
| Issue view | `gh issue view NUMBER` |
| Labels | `gh label list` / `gh label create` |
| Releases | `gh release list` / `gh release create` |
| Actions runs | `gh run list` / `gh run view` |

## Rules

- Use GitHub-native tooling for hosting operations.
- Do not invoke `tea`, Forgejo APIs, Forgejo Actions, or `git.starintel.actor` for
  Agent Zero workflows.
- Do not push credentials, token-bearing URLs, or auth output into logs, commits,
  PRs, or issues.
- Follow each repository's documented branch, PR, review, and CI requirements.
- Never bypass a red required check merely to land a change.
- Prefer exact-head checks before merge when the repository has concurrent work.
