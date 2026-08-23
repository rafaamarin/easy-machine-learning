from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RootCommandTests(unittest.TestCase):
    def test_root_shell_commands_are_executable_and_valid(self) -> None:
        for name in ("instalar.sh", "lanzar.sh", "verificar.sh"):
            path = REPO_ROOT / name
            self.assertTrue(path.is_file(), name)
            self.assertTrue(os.access(path, os.X_OK), name)
            completed = subprocess.run(
                ["sh", "-n", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_root_commands_resolve_the_book_relative_to_themselves(self) -> None:
        for name in ("instalar.sh", "lanzar.sh", "verificar.sh"):
            source = (REPO_ROOT / name).read_text(encoding="utf-8")
            self.assertIn('dirname -- "$0"', source)
            self.assertIn("libro_ml_dl", source)


if __name__ == "__main__":
    unittest.main()
