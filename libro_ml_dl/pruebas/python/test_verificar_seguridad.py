from __future__ import annotations

import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.verificar_seguridad import (
    _candidate_files,
    find_personal_paths,
    main,
    parse_secret_results,
    render_secret_findings,
    run_dependency_audit,
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
                patch(
                    "scripts.verificar_seguridad._candidate_files",
                    return_value=[repo_root / "nested" / "config.py"],
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

    def test_main_redacts_child_process_failure_details(self) -> None:
        sensitive_material = "".join(("synthetic", "-private", "-material"))
        with TemporaryDirectory() as directory:
            absolute_path = str(Path(directory) / "private-config")
            failure = subprocess.CalledProcessError(
                returncode=1,
                cmd=["scanner", absolute_path],
                output=sensitive_material,
                stderr=sensitive_material,
            )
            stdout = StringIO()
            stderr = StringIO()
            with (
                patch(
                    "scripts.verificar_seguridad.run_secret_scan",
                    return_value=[],
                ),
                patch(
                    "scripts.verificar_seguridad.find_personal_paths",
                    return_value=[],
                ),
                patch(
                    "scripts.verificar_seguridad.run_dependency_audit",
                    side_effect=failure,
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                result = main()

        rendered = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertEqual(
            stderr.getvalue(),
            "ERROR_SEGURIDAD: AUDITORIA_DEPENDENCIAS\n",
        )
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(sensitive_material, rendered)
        self.assertNotIn(absolute_path, rendered)

    def test_dependency_audit_captures_all_child_output(self) -> None:
        with TemporaryDirectory() as directory:
            book_root = Path(directory)
            with (
                patch(
                    "scripts.verificar_seguridad.shutil.which",
                    side_effect=["uv", "pip-audit"],
                ),
                patch("scripts.verificar_seguridad.subprocess.run") as run,
            ):
                run_dependency_audit(book_root)

        export_call, audit_call = run.call_args_list
        self.assertEqual(export_call.kwargs["stderr"], subprocess.PIPE)
        self.assertTrue(audit_call.kwargs["capture_output"])

    def test_secret_scan_uses_chunked_git_candidate_files(self) -> None:
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
            repo_root.joinpath("candidate-one.txt").write_text(
                "ordinary text",
                encoding="utf-8",
            )
            repo_root.joinpath("candidate-two.txt").write_text(
                "ordinary text",
                encoding="utf-8",
            )
            repo_root.joinpath("ignored.txt").write_text(
                "ordinary text",
                encoding="utf-8",
            )
            real_run = subprocess.run
            scanner_commands: list[list[str]] = []

            def run_safely(
                command: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                if command[0] == "git":
                    return real_run(command, **kwargs)
                scanner_commands.append(command)
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=json.dumps({"results": {}}),
                    stderr="",
                )

            with (
                patch(
                    "scripts.verificar_seguridad.shutil.which",
                    return_value="detect-secrets",
                ),
                patch(
                    "scripts.verificar_seguridad.SECRET_SCAN_CHUNK_SIZE",
                    1,
                    create=True,
                ),
                patch(
                    "scripts.verificar_seguridad.subprocess.run",
                    side_effect=run_safely,
                ),
            ):
                self.assertEqual(run_secret_scan(repo_root), [])

            self.assertTrue(scanner_commands)
            self.assertTrue(
                all("--all-files" not in command for command in scanner_commands)
            )
            scanned_paths = [
                path
                for command in scanner_commands
                for path in command[command.index("--") + 1 :]
            ]
            self.assertIn("candidate-one.txt", scanned_paths)
            self.assertIn("candidate-two.txt", scanned_paths)
            self.assertNotIn("ignored.txt", scanned_paths)
            self.assertTrue(
                all(
                    len(command[command.index("--") + 1 :]) == 1
                    for command in scanner_commands
                )
            )

    def test_git_candidate_inventory_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            repo_root.joinpath(".git").mkdir()
            failure = subprocess.CompletedProcess(
                ["git", "ls-files"],
                1,
                stdout=b"",
                stderr=b"internal details",
            )
            with patch(
                "scripts.verificar_seguridad.subprocess.run",
                return_value=failure,
            ):
                with self.assertRaisesRegex(RuntimeError, "inventario de Git"):
                    _candidate_files(repo_root)


if __name__ == "__main__":
    unittest.main()
