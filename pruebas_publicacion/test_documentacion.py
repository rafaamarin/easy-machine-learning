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


if __name__ == "__main__":
    unittest.main()
