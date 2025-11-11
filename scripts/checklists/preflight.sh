#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[preflight] %s\n' "$*"
}

commands=(
  "make check-runtime"
  "make lint"
  "make test"
  "make policy-check"
  "bash scripts/security/run_checkov.sh"
)

for cmd in "${commands[@]}"; do
  log "running: $cmd"
  eval "$cmd"
  log "ok: $cmd"
  echo
done

log "preflight checklist completed"
