from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 25 * 1024 * 1024
FORBIDDEN_PARTS = {".venv", "__pycache__", ".ruff_cache"}


def tracked_paths() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return [
        REPO_ROOT / item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    ]


class PublicationHygieneTests(unittest.TestCase):
    def test_no_tracked_file_is_a_symlink_or_oversized_artifact(self) -> None:
        for path in tracked_paths():
            self.assertFalse(path.is_symlink(), path.relative_to(REPO_ROOT))
            self.assertLessEqual(
                path.stat().st_size,
                MAX_TRACKED_BYTES,
                path.relative_to(REPO_ROOT),
            )

    def test_local_environments_and_runtime_downloads_are_not_tracked(
        self,
    ) -> None:
        for path in tracked_paths():
            relative = path.relative_to(REPO_ROOT)
            self.assertTrue(FORBIDDEN_PARTS.isdisjoint(relative.parts), relative)
            self.assertNotEqual(
                relative.as_posix(),
                "libro_ml_dl/configuracion/local.json",
            )
            if "assets/vendor/pyodide" in relative.as_posix():
                self.assertEqual(relative.name, ".gitkeep")

    def test_release_audit_exists_and_names_every_gate(self) -> None:
        source = REPO_ROOT.joinpath("docs/security-audit.md").read_text(
            encoding="utf-8"
        )
        for marker in (
            "detect-secrets 1.5.0",
            "pip-audit 2.10.1",
            "Historial Git",
            "Notebooks",
            "Clon limpio",
            "Revisión independiente",
            "Limitaciones",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
