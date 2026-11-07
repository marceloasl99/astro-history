#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI="$DIR/scripts/tools/tailwindcss"

if [ ! -f "$CLI" ]; then
    echo "Downloading Tailwind CSS Standalone CLI..."
    mkdir -p "$DIR/scripts/tools"
    curl -sL -o "$CLI" https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64
    chmod +x "$CLI"
fi

echo "Compiling production Tailwind CSS..."
"$CLI" -c "$DIR/tailwind.config.js" \
       -i "$DIR/src/web/static/css/tailwind.input.css" \
       -o "$DIR/src/web/static/css/tailwind.min.css" \
       --minify

echo "Success! Compiled to $DIR/src/web/static/css/tailwind.min.css ($(wc -c < "$DIR/src/web/static/css/tailwind.min.css") bytes)"
