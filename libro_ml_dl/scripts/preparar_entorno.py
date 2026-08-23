import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

PYODIDE_VERSION = "314.0.5"
CORE_ARCHIVE = f"pyodide-core-{PYODIDE_VERSION}.tar.bz2"
CORE_URL = (
    "https://github.com/pyodide/pyodide/releases/download/"
    f"{PYODIDE_VERSION}/{CORE_ARCHIVE}"
)
CORE_SHA256 = "f528dccea95fa8ec54295fd65bf86dd61183d11f0e52563dc8eadda45e0f78d6"  # pragma: allowlist secret  # noqa: E501
PACKAGE_BASE_URL = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"
REQUIRED_PACKAGES = ("numpy", "pandas", "matplotlib", "scikit-learn")
CORE_REQUIRED_FILES = (
    "pyodide.mjs",
    "pyodide.asm.mjs",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_package_closure(
    lock_data: dict[str, Any],
    requested: tuple[str, ...],
) -> list[str]:
    packages = lock_data["packages"]
    resolved: list[str] = []
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in resolved:
            return
        if name in visiting:
            raise ValueError(f"dependencia circular de Pyodide: {name}")
        if name not in packages:
            raise KeyError(f"paquete ausente del lock de Pyodide: {name}")
        visiting.add(name)
        for dependency in sorted(packages[name].get("depends", [])):
            visit(dependency)
        visiting.remove(name)
        resolved.append(name)

    for package in requested:
        visit(package)
    return resolved


def download_verified(url: str, target: Path, expected_sha256: str) -> None:
    if target.is_file():
        actual = sha256_file(target)
        if actual == expected_sha256:
            return
        raise ValueError(f"hash inválido en archivo existente: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="libro_pyodide_",
        dir=target.parent,
    ) as directory:
        temporary = Path(directory) / target.name
        with urllib.request.urlopen(url) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        actual = sha256_file(temporary)
        if actual != expected_sha256:
            raise ValueError(
                f"hash inválido para {target.name}: "
                f"esperado {expected_sha256}, recibido {actual}"
            )
        temporary.replace(target)


def validate_existing_runtime(vendor_dir: Path) -> dict[str, Any]:
    manifest_path = vendor_dir / "manifest.local.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("El manifest local de Pyodide no es válido.") from error

    if manifest.get("schema_version") != 1:
        raise RuntimeError("El manifest local tiene un esquema no compatible.")
    if manifest.get("pyodide_version") != PYODIDE_VERSION:
        raise RuntimeError(
            "Existe otro runtime. Muévelo fuera de assets/vendor/pyodide y repite."
        )
    if manifest.get("core_archive") != CORE_ARCHIVE:
        raise RuntimeError("El manifest local no corresponde al core fijado.")
    if manifest.get("core_sha256") != CORE_SHA256:
        raise RuntimeError("El manifest local no corresponde al hash core fijado.")
    if tuple(manifest.get("requested_packages", [])) != REQUIRED_PACKAGES:
        raise RuntimeError("El runtime local no contiene el conjunto fijado.")

    file_hashes = manifest.get("file_hashes")
    if not isinstance(file_hashes, dict):
        raise RuntimeError("El manifest local no contiene hashes de archivos válidos.")

    lock_path = vendor_dir / "pyodide-lock.json"
    lock_hash = file_hashes.get("pyodide-lock.json")
    if not isinstance(lock_hash, str) or not lock_path.is_file():
        raise RuntimeError("Runtime incompleto: falta pyodide-lock.json")
    if sha256_file(lock_path) != lock_hash:
        raise RuntimeError("Runtime corrupto o incompleto: pyodide-lock.json")
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        closure = resolve_package_closure(lock_data, REQUIRED_PACKAGES)
    except (json.JSONDecodeError, KeyError, ValueError, OSError) as error:
        raise RuntimeError("El lock local de Pyodide no es válido.") from error

    if manifest.get("package_closure") != closure:
        raise RuntimeError(
            "El manifest local no contiene el cierre de paquetes fijado."
        )

    package_hashes: dict[str, str] = {}
    try:
        for package_name in closure:
            package = lock_data["packages"][package_name]
            file_name = package["file_name"]
            expected_hash = package["sha256"]
            if not isinstance(file_name, str) or not isinstance(expected_hash, str):
                raise ValueError(package_name)
            package_hashes[file_name] = expected_hash
    except (KeyError, ValueError) as error:
        raise RuntimeError("El lock local de Pyodide no es válido.") from error

    expected_files = set(CORE_REQUIRED_FILES) | set(package_hashes)
    if set(file_hashes) != expected_files:
        raise RuntimeError("El manifest local no enumera exactamente el runtime.")

    for file_name in CORE_REQUIRED_FILES:
        expected_hash = file_hashes[file_name]
        file_path = vendor_dir / file_name
        if not isinstance(expected_hash, str) or not file_path.is_file():
            raise RuntimeError(f"Runtime incompleto: falta {file_name}")
        if sha256_file(file_path) != expected_hash:
            raise RuntimeError(f"Runtime corrupto o incompleto: {file_name}")

    for file_name, expected_hash in package_hashes.items():
        file_path = vendor_dir / file_name
        if file_hashes[file_name] != expected_hash:
            raise RuntimeError(f"El manifest local es inconsistente: {file_name}")
        if not file_path.is_file() or sha256_file(file_path) != expected_hash:
            raise RuntimeError(f"Runtime corrupto o incompleto: {file_name}")
    return manifest


def publish_runtime(staged_vendor_dir: Path, vendor_dir: Path) -> None:
    previous_vendor_dir = staged_vendor_dir.parent / "previous_pyodide"
    has_previous_runtime = vendor_dir.exists()
    if has_previous_runtime:
        vendor_dir.replace(previous_vendor_dir)
    try:
        staged_vendor_dir.replace(vendor_dir)
    except OSError as error:
        if has_previous_runtime:
            try:
                previous_vendor_dir.replace(vendor_dir)
            except OSError as rollback_error:
                raise RuntimeError(
                    "No se pudo publicar Pyodide ni restaurar el runtime anterior."
                ) from rollback_error
        raise RuntimeError(
            "No se pudo publicar el runtime local de Pyodide."
        ) from error


def prepare_runtime(vendor_dir: Path) -> dict[str, Any]:
    local_manifest_path = vendor_dir / "manifest.local.json"
    if local_manifest_path.is_file():
        return validate_existing_runtime(vendor_dir)

    unexpected = (
        [path for path in vendor_dir.iterdir() if path.name != ".gitkeep"]
        if vendor_dir.exists()
        else []
    )
    if unexpected:
        raise RuntimeError(
            "El directorio Pyodide contiene archivos sin manifest.local.json; "
            "no se sobrescriben."
        )
    vendor_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="libro_pyodide_stage_",
        dir=vendor_dir.parent,
    ) as directory:
        staging_root = Path(directory)
        staged_vendor_dir = staging_root / "pyodide"
        core_archive = staging_root / CORE_ARCHIVE
        download_verified(CORE_URL, core_archive, CORE_SHA256)
        with tarfile.open(core_archive, mode="r:bz2") as archive:
            archive.extractall(staging_root, filter="data")

        lock_path = staged_vendor_dir / "pyodide-lock.json"
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        closure = resolve_package_closure(lock_data, REQUIRED_PACKAGES)
        file_hashes = {
            file_name: sha256_file(staged_vendor_dir / file_name)
            for file_name in CORE_REQUIRED_FILES
        }
        for package_name in closure:
            package = lock_data["packages"][package_name]
            file_name = package["file_name"]
            expected_hash = package["sha256"]
            download_verified(
                PACKAGE_BASE_URL + file_name,
                staged_vendor_dir / file_name,
                expected_hash,
            )
            file_hashes[file_name] = expected_hash

        manifest = {
            "schema_version": 1,
            "pyodide_version": PYODIDE_VERSION,
            "core_archive": CORE_ARCHIVE,
            "core_sha256": CORE_SHA256,
            "requested_packages": list(REQUIRED_PACKAGES),
            "package_closure": closure,
            "file_hashes": file_hashes,
        }
        staged_vendor_dir.joinpath(".gitkeep").touch()
        staged_vendor_dir.joinpath("manifest.local.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        validate_existing_runtime(staged_vendor_dir)
        publish_runtime(staged_vendor_dir, vendor_dir)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara Pyodide para uso local.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma la descarga sin prompt.",
    )
    arguments = parser.parse_args()
    book_root = Path(__file__).resolve().parents[1]
    vendor_dir = book_root / "assets" / "vendor" / "pyodide"
    print(f"Pyodide: {PYODIDE_VERSION}")
    print(f"Destino: {vendor_dir}")
    if not arguments.yes:
        answer = input("¿Descargar el runtime local? [s/N] ").strip().lower()
        if answer not in {"s", "sí", "si", "y", "yes"}:
            print("Descarga cancelada; no se modificó el runtime.")
            return 0
    manifest = prepare_runtime(vendor_dir)
    package_count = len(manifest["package_closure"])
    print(
        "PYODIDE_LOCAL_OK "
        f"version={manifest['pyodide_version']} paquetes={package_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
