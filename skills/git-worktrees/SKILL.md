---
name: git-worktrees
description: git, worktrees, parallel-work, branch-isolation, pr-review, cleanup
compatibility: Requires git 2.22+ and Python 3.10+ (stdlib only).
---

# Git worktrees

## Goal

Give each branch or pull request its own checked-out directory under one
shared root, so parallel work never disturbs the primary checkout.

## Input

Run inside a git repository. Supply a branch name or a PR number:

- `--root DIR` overrides the worktree root; default `~/git/worktrees`,
  also configurable with `GIT_WORKTREE_ROOT`.
- `--base REF` creates a missing branch from `REF`; without it a missing
  branch is an error.
- `--pr N` fetches pull request `N` from `origin` into branch `pr/N`.
- `--dry-run` prints the plan without mutating anything.

## Output

    ~/git/worktrees/<project-slug>-<pr-or-branch-name>

`<project-slug>` comes from the repository directory name; separators in
branch names become `-`. Branch `feature/foo` in repository `my-app`
lands at `~/git/worktrees/my-app-feature-foo`; PR 12 lands at
`~/git/worktrees/my-app-pr-12`. Creating prints the new path.

## Workflow

Invoke `scripts/worktree.py` from this skill with `python3`:

```sh
python3 scripts/worktree.py add feature/foo --base main
python3 scripts/worktree.py add --pr 123
python3 scripts/worktree.py path feature/foo
python3 scripts/worktree.py list
python3 scripts/worktree.py remove my-app-feature-foo
python3 scripts/worktree.py prune
```

`remove` accepts a worktree directory name (looked up under the root),
a relative path, or an absolute path.

## Rules

- Only create or delete directories under the configured worktree root.
- Fail closed: never overwrite an existing directory, never delete
  branches, and never guess between reusing an existing branch and
  creating a new one; `--base` must say so explicitly.
- Never create a second worktree for a branch already checked out
  anywhere, and never remove the main working tree.
- `git worktree remove` refuses dirty or locked worktrees; pass
  `--force` only when the operator confirmed discarding the changes.
- Use the printed path as the single source of truth; never hand-build
  worktree directories outside this layout.
- When work ends, `remove` the worktree and `prune`; keep or delete
  branches by explicit choice, never as a side effect.

## Verification

```sh
git worktree list
git -C <worktree-path> status
```

The new path must appear registered and its status clean. For this
skills repository, also run `bash scripts/validate-skills`,
`bash scripts/validate-support-scripts`, and
`python3 -m unittest tests/test_git_worktrees.py -v`.
