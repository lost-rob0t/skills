# Deployment runbook

## Promote to production

1. Verify the CI badge on the pull request page is green.
2. Merge and deploy with `./deploy.sh prod`.

The badge in the README reflects the default branch: ![CI](https://ci.example/foo/bar/badge.svg)

If the deploy fails, the previous release directory is deleted by
`deploy.sh` before the new release is unpacked, so there is nothing to
roll back to; just fix forward and redeploy.
