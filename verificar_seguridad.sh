#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
exec uv run --locked --group security python scripts/verificar_seguridad.py
