#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: instala uv desde https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if ! uv python find '>=3.11' >/dev/null 2>&1; then
  echo "ERROR: se requiere Python 3.11 o posterior." >&2
  exit 1
fi

cd "$book_root"
uv sync --locked --group validation --group notebooks --group security
uv run python scripts/preparar_entorno.py "$@"
