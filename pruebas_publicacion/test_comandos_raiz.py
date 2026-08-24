from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


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

    def test_verifier_rejects_modified_staged_and_untracked_files(self) -> None:
        for state in ("modified", "staged", "untracked"):
            with self.subTest(state=state), TemporaryDirectory() as directory:
                temporary_root = Path(directory)
                repo_root = temporary_root / "repo"
                fake_bin = temporary_root / "bin"
                book_root = repo_root / "libro_ml_dl"
                repo_root.mkdir()
                fake_bin.mkdir()
                book_root.mkdir()
                verifier = repo_root / "verificar.sh"
                verifier.write_bytes(REPO_ROOT.joinpath("verificar.sh").read_bytes())
                verifier.chmod(0o755)
                tracked_file = repo_root / "tracked.txt"
                tracked_file.write_text("clean\n", encoding="utf-8")
                book_root.joinpath("placeholder.txt").write_text(
                    "book\n",
                    encoding="utf-8",
                )
                for command in ("uv", "node", "python3"):
                    executable = fake_bin / command
                    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                    executable.chmod(0o755)
                subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)
                subprocess.run(
                    ["git", "config", "user.email", "gate@example.invalid"],
                    cwd=repo_root,
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Gate Fixture"],
                    cwd=repo_root,
                    check=True,
                )
                subprocess.run(["git", "add", "--all"], cwd=repo_root, check=True)
                subprocess.run(
                    ["git", "commit", "--quiet", "-m", "clean fixture"],
                    cwd=repo_root,
                    check=True,
                )

                sensitive_name = "sensitive-fixture-name.txt"
                if state == "untracked":
                    repo_root.joinpath(sensitive_name).write_text(
                        "untracked\n",
                        encoding="utf-8",
                    )
                else:
                    tracked_file.write_text(f"{state}\n", encoding="utf-8")
                    if state == "staged":
                        subprocess.run(
                            ["git", "add", "tracked.txt"],
                            cwd=repo_root,
                            check=True,
                        )

                environment = os.environ.copy()
                environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
                completed = subprocess.run(
                    [str(verifier)],
                    cwd=repo_root,
                    check=False,
                    capture_output=True,
                    text=True,
                    env=environment,
                )

                rendered = completed.stdout + completed.stderr
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("árbol de trabajo", rendered)
                self.assertNotIn(sensitive_name, rendered)

    def test_verifier_uses_project_uv_python_for_publication_tests(self) -> None:
        source = REPO_ROOT.joinpath("verificar.sh").read_text(encoding="utf-8")
        self.assertIn('uv run --project "$book_root"', source)
        self.assertNotIn(
            "python3 -m unittest discover -s pruebas_publicacion",
            source,
        )


if __name__ == "__main__":
    unittest.main()
