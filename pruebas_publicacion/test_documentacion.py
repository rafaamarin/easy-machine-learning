from __future__ import annotations

import struct
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_required_publication_documents_exist(self) -> None:
        for relative_path in (
            "README.md",
            "LICENSE-CODE",
            "LICENSE-CONTENT",
            "CITATION.cff",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "REPRODUCIBILITY.md",
            "material_fuente/README.md",
        ):
            self.assertTrue((REPO_ROOT / relative_path).is_file(), relative_path)

    def test_readme_documents_clone_install_launch_and_verify(self) -> None:
        source = REPO_ROOT.joinpath("README.md").read_text(encoding="utf-8")
        for command in (
            "gh repo clone rafaamarin/easy-machine-learning",
            "./instalar.sh",
            "./lanzar.sh",
            "./verificar.sh",
            "./verificar_seguridad.sh",
        ):
            self.assertIn(command, source)
        self.assertIn("assets/branding/easy-machine-learning-banner.png", source)

    def test_banner_is_a_large_landscape_png(self) -> None:
        path = REPO_ROOT / "assets/branding/easy-machine-learning-banner.png"
        data = path.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertGreaterEqual(width, 1200)
        self.assertGreaterEqual(height, 600)
        self.assertGreater(width / height, 1.5)

    def test_licenses_cover_code_and_content(self) -> None:
        code_license = REPO_ROOT.joinpath("LICENSE-CODE").read_text(
            encoding="utf-8"
        )
        content_license = REPO_ROOT.joinpath("LICENSE-CONTENT").read_text(
            encoding="utf-8"
        )
        self.assertIn("MIT License", code_license)
        self.assertIn("Creative Commons Attribution 4.0", content_license)

    def test_citation_uses_code_license_without_release_date(self) -> None:
        source = REPO_ROOT.joinpath("CITATION.cff").read_text(encoding="utf-8")
        self.assertRegex(source, r"(?m)^license: MIT$")
        self.assertNotRegex(source, r"(?m)^date-released:")

    def test_content_license_boundary_remains_explicit(self) -> None:
        readme = REPO_ROOT.joinpath("README.md").read_text(encoding="utf-8")
        content_license = REPO_ROOT.joinpath("LICENSE-CONTENT").read_text(
            encoding="utf-8"
        )
        self.assertIn("[licencia MIT](LICENSE-CODE)", readme)
        self.assertIn(
            "[Creative Commons Attribution 4.0 Internacional](LICENSE-CONTENT)",
            readme,
        )
        self.assertIn(
            "educational text, notebooks, and visual assets", content_license
        )

    def test_download_zip_requires_git_clone_for_full_verification(self) -> None:
        source = REPO_ROOT.joinpath("README.md").read_text(encoding="utf-8")
        normalized_source = " ".join(source.split())
        self.assertIn(
            "El ZIP permite leer y ejecutar el proyecto", normalized_source
        )
        self.assertIn(
            "la verificación funcional y de seguridad completa requiere un "
            "clon Git autenticado",
            normalized_source,
        )

    def test_lightweight_mode_uses_only_the_safe_launcher(self) -> None:
        for relative_path in (
            "README.md",
            "REPRODUCIBILITY.md",
            "libro_ml_dl/README.md",
        ):
            source = REPO_ROOT.joinpath(relative_path).read_text(encoding="utf-8")
            self.assertNotIn("python3 -m http.server", source, relative_path)
        reproducibility = REPO_ROOT.joinpath("REPRODUCIBILITY.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("./lanzar.sh --sin-jupyter", reproducibility)

    def test_reproducibility_documents_managed_python_side_effects(self) -> None:
        source = REPO_ROOT.joinpath("REPRODUCIBILITY.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(source.split())
        self.assertIn(".python-version", source)
        self.assertIn("Python 3.11", source)
        self.assertIn("Python gestionado", normalized)
        self.assertIn("fuera del repositorio", normalized)


if __name__ == "__main__":
    unittest.main()
