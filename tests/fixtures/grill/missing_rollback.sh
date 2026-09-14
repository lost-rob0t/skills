#!/usr/bin/env bash
# Ship the release.
set -euo pipefail

release="$1"

# Remove the previous release to keep the target clean.
rm -rf "/srv/app/current"

tar -xzf "dist/${release}.tar.gz" -C /srv/app/current

systemctl restart app
