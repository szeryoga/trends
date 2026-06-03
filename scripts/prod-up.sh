#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Select action:"
echo "1. (Re)start all except trends-telegram"
echo "2. (Re)start all"
read "choice?Enter 1 or 2: "

case "$choice" in
  1)
    docker compose up -d --build postgres backend frontend
    ;;
  2)
    if [ -n "$(docker compose ps -q trends-telegram)" ]; then
      docker compose stop trends-telegram
    fi
    docker compose up -d --build postgres backend frontend
    docker compose build trends-telegram
    docker compose run --rm trends-telegram python -m app.auth_cli
    docker compose up -d trends-telegram
    ;;
  *)
    echo "Invalid choice: $choice" >&2
    exit 1
    ;;
esac
