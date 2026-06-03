#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Static checks require local dependencies inside containers or host environment."
echo "Suggested checks:"
echo "  docker compose -f docker-compose.yml -f docker-compose.local.yml build backend frontend"
echo "  docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm backend python -m compileall app"

