import runpy
import unittest
from pathlib import Path

BOOK_ROOT = Path(__file__).resolve().parents[2]


class Module00ContentTests(unittest.TestCase):
    def test_first_experiment_has_expected_improvement(self) -> None:
        namespace = runpy.run_path(
            BOOK_ROOT
            / "contenido_fuente"
            / "00_inicio"
            / "labs"
            / "00_primer_experimento.py"
        )
        self.assertEqual(namespace["tiempos_min"].shape, (5,))
        self.assertEqual(namespace["mejora_min"], 4.0)

    def test_page_contains_active_learning_contract(self) -> None:
        source = (BOOK_ROOT / "contenido_fuente" / "00_inicio" / "index.md").read_text(
            encoding="utf-8"
        )
        markers = (
            'data-pedagogy="reto"',
            'data-pedagogy="modifica"',
            "data-solution",
        )
        for marker in markers:
            self.assertIn(marker, source)
        self.assertIn('data-static-output-for="00_primer_experimento"', source)
