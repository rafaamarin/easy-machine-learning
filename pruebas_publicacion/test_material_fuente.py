from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "material_fuente/notebooks/01-series-dataframes.ipynb": (
        "15f0a0f4137ba81117f8bacf90dbd341"  # pragma: allowlist secret
        "828335963191b2fdc3a213650df510ea"  # pragma: allowlist secret
    ),
    "material_fuente/notebooks/07-estadisticas-basicas.ipynb": (
        "f4352008a8f973f496dba58c08740b25"  # pragma: allowlist secret
        "0daac81b20b94ba3b1eac86b2221e30a"  # pragma: allowlist secret
    ),
    "material_fuente/notebooks/05-scale.ipynb": (
        "894a588d2eb24d02d032ac61a2f2961e"  # pragma: allowlist secret
        "ef1920a9c6cfdb17e50948d0612dbeaf"  # pragma: allowlist secret
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceMaterialTests(unittest.TestCase):
    def test_notebooks_are_byte_identical_to_approved_sources(self) -> None:
        for relative_path, expected_hash in EXPECTED_HASHES.items():
            self.assertEqual(sha256_file(REPO_ROOT / relative_path), expected_hash)

    def test_notebook_inventory_contains_exactly_the_three_approved_files(
        self,
    ) -> None:
        completed = subprocess.run(
            ["git", "ls-files", "-z", "*.ipynb"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        actual = {
            item.decode("utf-8")
            for item in completed.stdout.split(b"\0")
            if item
        }
        self.assertEqual(actual, set(EXPECTED_HASHES))

    def test_source_map_uses_repository_relative_notebook_paths(self) -> None:
        source_map_path = (
            REPO_ROOT / "libro_ml_dl/contenido_fuente/mapa_fuentes.json"
        )
        source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
        sources = source_map["modules"]["01_datos_y_formas"]["sources"]
        self.assertEqual(
            sources,
            [
                "material_fuente/notebooks/01-series-dataframes.ipynb",
                "material_fuente/notebooks/07-estadisticas-basicas.ipynb",
                "material_fuente/notebooks/05-scale.ipynb",
            ],
        )


if __name__ == "__main__":
    unittest.main()
