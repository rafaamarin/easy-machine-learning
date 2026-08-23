from __future__ import annotations

import json
import re
from pathlib import Path

if __package__:
    from scripts.construir_contenido import LAB_PATTERN
    from scripts.modelo_contenido import (
        load_manifest,
        resolve_vault_root,
        validate_manifest,
        validate_source_map,
    )
else:
    from construir_contenido import LAB_PATTERN
    from modelo_contenido import (
        load_manifest,
        resolve_vault_root,
        validate_manifest,
        validate_source_map,
    )

PEDAGOGICAL_MARKERS = {
    "reto",
    "observa",
    "matematica",
    "modifica",
    "desde_cero",
    "con_herramienta",
    "depura",
    "comprueba",
}


def validate_learning_source(
    source_path: Path,
    required_markers: set[str],
    book_root: Path,
) -> list[str]:
    source = source_path.read_text(encoding="utf-8")
    errors: list[str] = []
    for marker in sorted(required_markers):
        if f'data-pedagogy="{marker}"' not in source:
            errors.append(f"{source_path}: falta data-pedagogy={marker}")
    if "data-solution" not in source:
        errors.append(f"{source_path}: falta solución colapsable")
    if "data-progress-id" not in source:
        errors.append(f"{source_path}: falta checklist persistente")
    if "/Users/" in source or re.search(r"[A-Za-z]:[\\\\/]", source):
        errors.append(f"{source_path}: contiene ruta absoluta")
    lab_matches = list(LAB_PATTERN.finditer(source))
    if source.count("<py-lab ") != len(lab_matches):
        errors.append(f"{source_path}: etiqueta py-lab mal formada")
    resolved_book_root = book_root.resolve()
    for match in lab_matches:
        lab_path = (book_root / match.group("src")).resolve()
        lab_id = match.group("lab_id")
        if not lab_path.is_relative_to(resolved_book_root):
            errors.append(f"{source_path}: lab fuera del libro")
        elif not lab_path.is_file():
            errors.append(f"{source_path}: lab no existe: {match.group('src')}")
        if f'data-static-output-for="{lab_id}"' not in source:
            errors.append(f"{source_path}: falta salida estática para {lab_id}")
    return errors


def main() -> int:
    book_root = Path(__file__).resolve().parents[1]
    vault_root = resolve_vault_root(book_root)
    manifest = load_manifest(book_root)
    source_map_path = book_root / "contenido_fuente" / "mapa_fuentes.json"
    source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
    errors = [
        *validate_manifest(manifest, book_root),
        *validate_source_map(source_map, manifest, vault_root),
    ]
    for module in manifest["modules"]:
        if module["status"] != "disponible":
            continue
        source_path = book_root / str(module["source"])
        if module["id"] == "01_datos_y_formas":
            required_markers = PEDAGOGICAL_MARKERS
        else:
            required_markers = {"reto", "observa", "modifica", "comprueba"}
        errors.extend(
            validate_learning_source(source_path, required_markers, book_root)
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("VALIDACION_ESTATICA_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
