import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.construir_contenido import build_site, expand_lab_tags


class ContentBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_expands_lab_source_inside_book_root(self) -> None:
        lab_path = self.root / "contenido_fuente" / "demo.py"
        lab_path.parent.mkdir(parents=True)
        lab_path.write_text("print(2 + 2)\n", encoding="utf-8")
        tag = (
            '<py-lab data-lab-id="demo" '
            'data-src="contenido_fuente/demo.py" '
            'data-packages="" data-title="Suma"></py-lab>'
        )
        html = expand_lab_tags(tag, self.root)
        self.assertIn('data-python-lab="demo"', html)
        self.assertIn("print(2 + 2)", html)
        self.assertIn("Ejecutar", html)

    def test_check_mode_detects_stale_generated_html(self) -> None:
        self._write_fixture_book()
        build_site(self.root)
        source = self.root / "contenido_fuente" / "00_inicio" / "index.md"
        source.write_text("# Cambio\n", encoding="utf-8")
        stale = build_site(self.root, check=True)
        self.assertEqual([self.root / "index.html"], stale)

    def test_rejects_lab_path_outside_book_root(self) -> None:
        tag = (
            '<py-lab data-lab-id="escape" data-src="../escape.py" '
            'data-packages="" data-title="Escape"></py-lab>'
        )
        with self.assertRaisesRegex(ValueError, "lab fuera del libro"):
            expand_lab_tags(tag, self.root)

    def test_builder_never_writes_to_an_escaped_output(self) -> None:
        self._write_fixture_book()
        manifest_path = self.root / "contenido_fuente" / "manifiesto.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        outside_output = self.root.parent / "outside.html"
        manifest["modules"][0]["output"] = "../outside.html"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with patch("scripts.construir_contenido.validate_manifest", return_value=[]):
            with self.assertRaisesRegex(ValueError, "fuera del libro"):
                build_site(self.root)

        self.assertFalse(outside_output.exists())

    def test_direct_file_cli_builds_from_book_root(self) -> None:
        book_root = Path(__file__).resolve().parents[2]
        completed = subprocess.run(
            [sys.executable, "scripts/construir_contenido.py"],
            cwd=book_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("GENERADO: index.html", completed.stdout)

    def _write_fixture_book(self) -> None:
        source = self.root / "contenido_fuente" / "00_inicio" / "index.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Inicio\n\nEjecuta algo.\n", encoding="utf-8")
        template = self.root / "assets" / "plantillas" / "pagina.html"
        template.parent.mkdir(parents=True)
        template.write_text(
            "<html><head><title>$page_title</title></head>"
            "<body>$module_navigation<main>$content_html</main>"
            "<!-- source_sha256: $source_sha256 --></body></html>",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 1,
            "content_version": "0.1.0",
            "modules": [
                {
                    "id": "00_inicio",
                    "number": "00",
                    "title": "Inicio",
                    "status": "disponible",
                    "duration_minutes": 10,
                    "prerequisites": [],
                    "execution_mode": "pyodide",
                    "source": "contenido_fuente/00_inicio/index.md",
                    "output": "index.html",
                    "sections": ["inicio"],
                }
            ],
        }
        (self.root / "contenido_fuente" / "manifiesto.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
