from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_STATUSES = {"en_construccion", "disponible", "planificado"}
VALID_EXECUTION_MODES = {"ninguno", "pyodide", "jupyter", "mixto"}
REQUIRED_MODULE_KEYS = {
    "id",
    "number",
    "title",
    "status",
    "duration_minutes",
    "prerequisites",
    "execution_mode",
    "source",
    "output",
    "sections",
}


def resolve_confined_path(root: Path, value: str, boundary: str) -> Path:
    """Resuelve una ruta relativa sin permitir salidas del límite indicado."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"ruta inválida para el {boundary}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"ruta fuera del {boundary}: {value}")
    resolved_root = root.resolve()
    resolved_path = (resolved_root / path).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise ValueError(f"ruta fuera del {boundary}: {value}")
    return resolved_path


def resolve_book_path(root: Path, value: str) -> Path:
    return resolve_confined_path(root, value, "libro")


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / "contenido_fuente" / "manifiesto.json"
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_vault_root(book_root: Path) -> Path:
    """Resuelve la raíz local del vault para validar la procedencia."""
    configuration_path = book_root / "configuracion" / "local.json"
    if not configuration_path.is_file():
        return book_root.parent

    try:
        configuration = json.loads(configuration_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("configuracion/local.json no contiene JSON válido") from error

    if not isinstance(configuration, dict):
        raise ValueError("configuracion/local.json debe contener un objeto JSON")

    vault_root_value = configuration.get("vault_root")
    if vault_root_value is None:
        return book_root.parent
    if not isinstance(vault_root_value, str) or not vault_root_value.strip():
        raise ValueError("vault_root debe ser una ruta de directorio no vacía")

    vault_root = Path(vault_root_value).expanduser()
    if not vault_root.is_absolute():
        vault_root = book_root / vault_root
    if not vault_root.is_dir():
        raise ValueError(f"vault_root no es un directorio existente: {vault_root}")
    return vault_root


def _cycle_errors(modules_by_id: dict[str, dict[str, Any]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    errors: list[str] = []

    def visit(module_id: str, trail: tuple[str, ...]) -> None:
        if module_id in visiting:
            cycle = " -> ".join((*trail, module_id))
            errors.append(f"ciclo de prerequisitos: {cycle}")
            return
        if module_id in visited:
            return
        visiting.add(module_id)
        for prerequisite in modules_by_id[module_id]["prerequisites"]:
            if prerequisite in modules_by_id:
                visit(prerequisite, (*trail, module_id))
        visiting.remove(module_id)
        visited.add(module_id)

    for module_id in modules_by_id:
        visit(module_id, ())
    return errors


def validate_manifest(manifest: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")
    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        return [*errors, "modules debe ser una lista no vacía"]

    module_ids = [module.get("id") for module in modules]
    duplicates = {
        value
        for value in module_ids
        if isinstance(value, str) and module_ids.count(value) > 1
    }
    for module_id in sorted(duplicates):
        errors.append(f"module id duplicado: {module_id}")

    modules_by_id: dict[str, dict[str, Any]] = {}
    for module in modules:
        missing = REQUIRED_MODULE_KEYS - module.keys()
        if missing:
            errors.append(f"{module.get('id', '<sin id>')}: faltan {sorted(missing)}")
            continue
        module_id = module["id"]
        modules_by_id[module_id] = module
        if module["status"] not in VALID_STATUSES:
            errors.append(f"{module_id}: status inválido")
        if module["execution_mode"] not in VALID_EXECUTION_MODES:
            errors.append(f"{module_id}: execution_mode inválido")
        duration = module["duration_minutes"]
        if not isinstance(duration, int) or duration <= 0:
            errors.append(f"{module_id}: duration_minutes debe ser positivo")
        for field in ("source", "output"):
            value = module[field]
            if value is None:
                if module["status"] == "disponible":
                    errors.append(f"{module_id}: {field} obligatorio")
                continue
            if not isinstance(value, str) or not value:
                errors.append(f"{module_id}: {field} obligatorio")
                continue
            try:
                path = resolve_book_path(root, value)
            except ValueError:
                errors.append(f"{module_id}: {field} fuera del libro: {value}")
                continue
            if field == "source" and module["status"] == "disponible":
                if not path.is_file():
                    errors.append(f"{module_id}: source no existe: {value}")

    known_ids = set(modules_by_id)
    for module_id, module in modules_by_id.items():
        for prerequisite in module["prerequisites"]:
            if prerequisite not in known_ids:
                errors.append(f"{module_id}: prerequisito desconocido: {prerequisite}")
    errors.extend(_cycle_errors(modules_by_id))
    return errors


def validate_source_map(
    source_map: dict[str, Any],
    manifest: dict[str, Any],
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    mapped_modules = source_map.get("modules", {})
    tracked_statuses = {"en_construccion", "disponible"}
    for module in manifest["modules"]:
        if module["status"] not in tracked_statuses:
            continue
        module_id = module["id"]
        if module_id not in mapped_modules:
            errors.append(f"{module_id}: falta mapa de fuentes")
            continue
        for source in mapped_modules[module_id].get("sources", []):
            if Path(source).is_absolute():
                errors.append(f"{module_id}: fuente absoluta no permitida: {source}")
                continue
            try:
                source_path = resolve_confined_path(repo_root, source, "vault")
            except ValueError:
                errors.append(f"{module_id}: fuente fuera del vault: {source}")
                continue
            if not source_path.is_file():
                errors.append(f"{module_id}: fuente no existe: {source}")
    return errors
