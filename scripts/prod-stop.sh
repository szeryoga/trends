#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Select action:"
echo "1. Stop all except trends-telegram"
echo "2. Stop all"
read "choice?Enter 1 or 2: "

case "$choice" in
  1)
    docker compose stop postgres backend frontend
    ;;
  2)
    docker compose stop postgres backend frontend trends-telegram
    ;;
  *)
    echo "Invalid choice: $choice" >&2
    exit 1
    ;;
esac
