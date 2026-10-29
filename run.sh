#!/usr/bin/env bash
# Script de Inicialização da Plataforma AstroHistory (Porta 81)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌌 Iniciando AstroHistory Web Server na porta 81..."
exec "$SCRIPT_DIR/.venv/bin/uvicorn" src.web.app:app --host 0.0.0.0 --port 81
