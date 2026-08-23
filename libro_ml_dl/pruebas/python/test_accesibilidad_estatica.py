import re
import unittest
from pathlib import Path

BOOK_ROOT = Path(__file__).resolve().parents[2]


class StaticAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (BOOK_ROOT / "index.html").read_text(encoding="utf-8")
        module_path = BOOK_ROOT / "contenido" / "01_datos_y_formas" / "index.html"
        module_html = module_path.read_text(encoding="utf-8")
        cls.generated_pages = [cls.html, module_html]

    def test_has_spanish_language_and_landmarks(self) -> None:
        self.assertIn('<html lang="es"', self.html)
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('aria-label="Módulos del libro"', self.html)
        self.assertIn('<main id="contenido"', self.html)

    def test_index_lists_every_module(self) -> None:
        for number in [f"{value:02d}." for value in range(15)]:
            self.assertIn(number, self.html)
        self.assertIn("A. Glosario y apéndices", self.html)
        self.assertIn("Índice completo", self.html)
        self.assertIn("45 min", self.html)
        self.assertIn("Prerequisitos", self.html)

    def test_only_built_modules_are_links(self) -> None:
        self.assertIn('href="index.html">00. Inicio y mapa</a>', self.html)
        self.assertIn(
            'href="contenido/01_datos_y_formas/index.html">'
            "01. Datos, formas y señales</a>",
            self.html,
        )
        self.assertIn('aria-disabled="true">02. Una recta que aprende', self.html)

    def test_interactive_controls_have_accessible_names(self) -> None:
        for html in self.generated_pages:
            self.assertNotRegex(html, r"<textarea(?![^>]*aria-label)")
            self.assertNotRegex(html, r"<img(?![^>]*alt=)")

    def test_progress_ids_are_unique(self) -> None:
        combined = "\n".join(self.generated_pages)
        progress_ids = re.findall(r'data-progress-id="([^"]+)"', combined)
        self.assertEqual(len(progress_ids), len(set(progress_ids)))

    def test_solutions_are_collapsible(self) -> None:
        module = self.generated_pages[1]
        self.assertGreaterEqual(module.count("<details"), 3)
        self.assertIn("data-solution", module)
