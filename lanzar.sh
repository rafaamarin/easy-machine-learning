#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: ejecuta ./instalar.sh después de instalar uv." >&2
  exit 1
fi

cd "$book_root"
exec uv run --locked --group notebooks python scripts/lanzar.py "$@"
