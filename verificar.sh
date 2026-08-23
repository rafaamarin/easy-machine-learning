#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
uv run --locked --group validation --group notebooks \
  python scripts/verificar_corte_01.py
