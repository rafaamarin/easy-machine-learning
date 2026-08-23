import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.modelo_contenido import (
    resolve_vault_root,
    validate_manifest,
    validate_source_map,
)


class ManifestValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_rejects_duplicate_module_ids(self) -> None:
        module = {
            "id": "00_inicio",
            "number": "00",
            "title": "Inicio",
            "status": "planificado",
            "duration_minutes": 10,
            "prerequisites": [],
            "execution_mode": "pyodide",
            "source": None,
            "output": None,
            "sections": [],
        }
        errors = validate_manifest(
            {
                "schema_version": 1,
                "content_version": "0.1.0",
                "modules": [module, module],
            },
            self.root,
        )
        self.assertIn("module id duplicado: 00_inicio", errors)

    def test_rejects_prerequisite_cycles(self) -> None:
        modules = [
            self._module("00_inicio", ["01_datos_y_formas"]),
            self._module("01_datos_y_formas", ["00_inicio"]),
        ]
        errors = validate_manifest(
            {"schema_version": 1, "content_version": "0.1.0", "modules": modules},
            self.root,
        )
        self.assertTrue(any("ciclo de prerequisitos" in error for error in errors))

    def test_rejects_absolute_provenance_paths(self) -> None:
        module = self._module("00_inicio", [])
        module["status"] = "en_construccion"
        manifest = {
            "schema_version": 1,
            "content_version": "0.1.0",
            "modules": [module],
        }
        source_map = {
            "schema_version": 1,
            "modules": {
                "00_inicio": {
                    "sources": ["/Users/example/source.ipynb"],
                    "transformation": "test",
                }
            },
        }
        errors = validate_source_map(source_map, manifest, self.root)
        self.assertTrue(
            any("fuente absoluta no permitida" in error for error in errors)
        )

    def test_rejects_provenance_parent_and_symlink_escapes(self) -> None:
        vault_root = self.root / "vault"
        vault_root.mkdir()
        outside_source = self.root / "outside.ipynb"
        outside_source.write_text("external", encoding="utf-8")
        link = vault_root / "linked.ipynb"
        link.symlink_to(outside_source)
        module = self._module("00_inicio", [])
        module["status"] = "en_construccion"
        source_map = {
            "schema_version": 1,
            "modules": {
                "00_inicio": {
                    "sources": ["../outside.ipynb", "linked.ipynb"],
                    "transformation": "test",
                }
            },
        }

        errors = validate_source_map(
            source_map,
            {"schema_version": 1, "content_version": "0.1.0", "modules": [module]},
            vault_root,
        )

        self.assertEqual(len(errors), 2)
        self.assertTrue(all("fuera del vault" in error for error in errors))

    def test_rejects_manifest_source_and_output_escapes(self) -> None:
        book_root = self.root / "libro_ml_dl"
        book_root.mkdir()
        outside_source = self.root / "outside.md"
        outside_source.write_text("external", encoding="utf-8")
        inside = book_root / "contenido_fuente"
        inside.mkdir()
        (inside / "linked.md").symlink_to(outside_source)
        for source, output in (
            (str(outside_source), "index.html"),
            ("../outside.md", "index.html"),
            ("contenido_fuente/linked.md", "../outside.html"),
        ):
            module = self._module("00_inicio", [])
            module.update({"status": "disponible", "source": source, "output": output})
            errors = validate_manifest(
                {"schema_version": 1, "content_version": "0.1.0", "modules": [module]},
                book_root,
            )
            self.assertTrue(any("fuera del libro" in error for error in errors))

    def test_rejects_escaped_paths_in_non_available_module(self) -> None:
        module = self._module("00_inicio", [])
        module.update(
            {
                "status": "en_construccion",
                "source": "../source.md",
                "output": "../output.html",
            }
        )

        errors = validate_manifest(
            {"schema_version": 1, "content_version": "0.1.0", "modules": [module]},
            self.root,
        )

        self.assertEqual(
            [
                "00_inicio: source fuera del libro: ../source.md",
                "00_inicio: output fuera del libro: ../output.html",
            ],
            errors,
        )

    @staticmethod
    def _module(module_id: str, prerequisites: list[str]) -> dict[str, object]:
        return {
            "id": module_id,
            "number": module_id.split("_")[0],
            "title": module_id,
            "status": "planificado",
            "duration_minutes": 10,
            "prerequisites": prerequisites,
            "execution_mode": "pyodide",
            "source": None,
            "output": None,
            "sections": [],
        }


class VaultRootResolutionTests(unittest.TestCase):
    def test_defaults_to_book_parent_without_local_configuration(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            vault_root = Path(temporary_directory)
            book_root = vault_root / "libro_ml_dl"
            book_root.mkdir()

            self.assertEqual(resolve_vault_root(book_root), vault_root)

    def test_uses_explicit_directory_from_local_configuration(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            book_root = root / "libro_ml_dl"
            explicit_vault_root = root / "vault_externo"
            book_root.mkdir()
            explicit_vault_root.mkdir()
            configuration_directory = book_root / "configuracion"
            configuration_directory.mkdir()
            (configuration_directory / "local.json").write_text(
                json.dumps({"vault_root": str(explicit_vault_root)}),
                encoding="utf-8",
            )

            self.assertEqual(resolve_vault_root(book_root), explicit_vault_root)

    def test_rejects_non_directory_vault_root_from_local_configuration(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            book_root = root / "libro_ml_dl"
            book_root.mkdir()
            configuration_directory = book_root / "configuracion"
            configuration_directory.mkdir()
            invalid_vault_root = root / "not_a_directory"
            invalid_vault_root.write_text("not a directory", encoding="utf-8")
            (configuration_directory / "local.json").write_text(
                json.dumps({"vault_root": str(invalid_vault_root)}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "vault_root.*directorio"):
                resolve_vault_root(book_root)
