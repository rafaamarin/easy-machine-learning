from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

if __package__:
    from scripts.preparar_entorno import validate_existing_runtime
else:
    from preparar_entorno import validate_existing_runtime

BOOK_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=BOOK_ROOT, check=True)


def main() -> int:
    node = shutil.which("node")
    ruff = shutil.which("ruff")
    if node is None:
        print("ERROR: Node es necesario solo para las pruebas JS.", file=sys.stderr)
        return 1
    if ruff is None:
        print(
            "ERROR: ejecuta 'uv sync --group validation' para instalar Ruff.",
            file=sys.stderr,
        )
        return 1

    vendor_dir = BOOK_ROOT / "assets" / "vendor" / "pyodide"
    worker = vendor_dir / "pyodide.mjs"
    manifest = vendor_dir / "manifest.local.json"
    if not worker.is_file() or not manifest.is_file():
        print(
            "ERROR: ejecuta 'uv run python scripts/preparar_entorno.py'.",
            file=sys.stderr,
        )
        return 1
    try:
        validate_existing_runtime(vendor_dir)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    python = sys.executable
    run([ruff, "check", "scripts", "pruebas", "contenido_fuente"])
    run([ruff, "format", "--check", "scripts", "pruebas", "contenido_fuente"])
    run(
        [
            python,
            "-m",
            "unittest",
            "discover",
            "-s",
            "pruebas/python",
            "-p",
            "test_*.py",
            "-v",
        ]
    )
    js_tests = [
        str(path) for path in sorted((BOOK_ROOT / "pruebas" / "js").glob("*.test.mjs"))
    ]
    run([node, "--test", *js_tests])
    run([python, "scripts/validar_contenido.py"])
    run([python, "scripts/construir_contenido.py", "--check"])
    print("CORTE_01_VALIDACION_LOCAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
