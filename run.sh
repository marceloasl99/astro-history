#!/usr/bin/env bash
# Script de Inicialização da Plataforma AstroHistory (Localhost Seguro)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="${ASTRO_HOST:-127.0.0.1}"
PORT="${ASTRO_PORT:-8000}"

echo "🌌 Iniciando AstroHistory Web Server em http://${HOST}:${PORT}..."
exec "$SCRIPT_DIR/.venv/bin/uvicorn" src.web.app:app --host "$HOST" --port "$PORT"
