#!/usr/bin/env bash
# Reconcile the ledger every minute.
set -euo pipefail

while true; do
  if ! ledger-sync --push-remote; then
    # Transient network errors are common; keep retrying until it works.
    sleep 5
    continue
  fi
  sleep 60
done
