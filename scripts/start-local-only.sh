#!/usr/bin/env bash
set -euo pipefail

export LOCAL_ONLY_MODE=true
export NEXT_PUBLIC_LOCAL_ONLY_MODE=true
export LOCAL_ONLY_WORKDIR="${LOCAL_ONLY_WORKDIR:-$PWD}"

echo "Starting HackWithAI v2 in local-only mode"
echo "LOCAL_ONLY_WORKDIR=${LOCAL_ONLY_WORKDIR}"
echo "Open: http://localhost:3002"

pnpm exec next dev --turbopack --hostname 0.0.0.0 --port 3002
