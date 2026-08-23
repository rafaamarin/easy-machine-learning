from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.verificar_seguridad import (
    find_personal_paths,
    parse_secret_results,
    render_secret_findings,
    run_secret_scan,
)


class SecurityVerificationTests(unittest.TestCase):
    def test_secret_report_never_contains_the_candidate_value(self) -> None:
        candidate = "example-sensitive-value"
        payload = {
            "results": {
                "config.py": [
                    {
                        "type": "Secret Keyword",
                        "line_number": 7,
                        "hashed_secret": candidate,
                    }
                ]
            }
        }
        findings = parse_secret_results(payload)
        report = render_secret_findings(findings)
        self.assertEqual(report, ["config.py:7 [Secret Keyword]"])
        self.assertNotIn(candidate, "\n".join(report))

    def test_detects_only_personal_absolute_paths_in_tracked_text(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            repo_root.joinpath("safe.txt").write_text(
                "/Users/example/project",
                encoding="utf-8",
            )
            private_path = repo_root / "private.txt"
            private_marker = "/".join(("", "Users", "rafa", "Documents"))
            private_path.write_text(private_marker, encoding="utf-8")
            self.assertEqual(find_personal_paths(repo_root), [private_path])

    def test_ignores_ephemeral_superpowers_workspace(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            excluded_directory = repo_root / ".superpowers" / "sdd"
            excluded_directory.mkdir(parents=True)
            private_marker = "/".join(("", "Users", "rafa", "Documents"))
            excluded_directory.joinpath("brief.md").write_text(
                private_marker,
                encoding="utf-8",
            )
            self.assertEqual(find_personal_paths(repo_root), [])

    def test_secret_scan_normalizes_finding_paths_to_repo_relative(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            payload = {
                "results": {
                    str(repo_root / "nested" / "config.py"): [
                        {"type": "Secret Keyword", "line_number": 4}
                    ]
                }
            }
            with (
                patch(
                    "scripts.verificar_seguridad.shutil.which",
                    return_value="detect-secrets",
                ),
                patch("scripts.verificar_seguridad.subprocess.run") as run,
            ):
                run.return_value.stdout = json.dumps(payload)
                findings = run_secret_scan(repo_root)

            self.assertEqual(
                render_secret_findings(findings),
                ["nested/config.py:4 [Secret Keyword]"],
            )

    def test_personal_path_scan_ignores_git_ignored_files(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repo_root,
                check=True,
            )
            repo_root.joinpath(".gitignore").write_text(
                "ignored.txt\n",
                encoding="utf-8",
            )
            private_marker = "/".join(("", "Users", "rafa", "Documents"))
            repo_root.joinpath("ignored.txt").write_text(
                private_marker,
                encoding="utf-8",
            )

            self.assertEqual(find_personal_paths(repo_root), [])

    def test_personal_path_scan_excludes_only_pyodide_vendor_files(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            vendor_root = repo_root / "libro_ml_dl" / "assets" / "vendor"
            pyodide_file = vendor_root / "pyodide" / "runtime.txt"
            candidate_file = vendor_root / "other" / "config.txt"
            pyodide_file.parent.mkdir(parents=True)
            candidate_file.parent.mkdir(parents=True)
            private_marker = "/".join(("", "Users", "rafa", "Documents"))
            pyodide_file.write_text(private_marker, encoding="utf-8")
            candidate_file.write_text(private_marker, encoding="utf-8")

            self.assertEqual(find_personal_paths(repo_root), [candidate_file])


if __name__ == "__main__":
    unittest.main()
