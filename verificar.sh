#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
uv run --locked --group validation --group notebooks --group security \
  python -m unittest discover -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
uv run --locked --group validation ruff check scripts pruebas contenido_fuente
uv run --locked --group validation ruff format --check \
  scripts pruebas contenido_fuente
uv run --locked --group validation python scripts/verificar_corte_01.py
uv run --locked --group validation --group notebooks \
  python scripts/validar_notebooks.py

cd "$repo_root"
python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
git diff --check
printf '%s\n' 'VERIFICACION_COMPLETA_OK'
