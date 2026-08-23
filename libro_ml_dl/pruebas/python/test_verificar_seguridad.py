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
    HistoricalFinding,
    HistoricalScanError,
    SecretFinding,
    _candidate_files,
    _is_adjudicated_checksum,
    find_personal_paths,
    main,
    parse_secret_results,
    render_historical_findings,
    render_secret_findings,
    run_dependency_audit,
    run_secret_scan,
    scan_git_history,
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

    def test_git_candidate_inventory_rejects_non_utf8_filenames(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            repo_root.joinpath(".git").mkdir()
            inventory = subprocess.CompletedProcess(
                ["git", "ls-files"],
                0,
                stdout=b"invalid-\xff-name\0",
                stderr=b"",
            )
            with patch(
                "scripts.verificar_seguridad.subprocess.run",
                return_value=inventory,
            ):
                with self.assertRaisesRegex(RuntimeError, "UTF-8"):
                    _candidate_files(repo_root)

    def test_git_candidate_inventory_rejects_symlinks(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo_root = root / "repo"
            repo_root.mkdir()
            external_file = root / "external.txt"
            external_file.write_text("ordinary text", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)
            repo_root.joinpath("linked.txt").symlink_to(external_file)
            subprocess.run(
                ["git", "add", "linked.txt"],
                cwd=repo_root,
                check=True,
            )

            with self.assertRaisesRegex(RuntimeError, "enlace simbólico"):
                _candidate_files(repo_root)

    def test_redacted_rendering_escapes_filename_controls(self) -> None:
        report = render_secret_findings(
            [SecretFinding("unsafe\nname.py", 3, "Detector\rName")]
        )
        self.assertEqual(report, ["unsafe\\nname.py:3 [Detector\\rName]"])

    def test_checksum_adjudication_requires_detector_and_context(self) -> None:
        with TemporaryDirectory() as directory:
            snapshot_root = Path(directory)
            source_path = snapshot_root / "libro_ml_dl/scripts/preparar_entorno.py"
            source_path.parent.mkdir(parents=True)
            lines = ["" for _ in range(16)]
            lines.append('NOT_A_CHECKSUM = "' + "ab" * 32 + '"')
            source_path.write_text("\n".join(lines), encoding="utf-8")
            finding = SecretFinding(
                "libro_ml_dl/scripts/preparar_entorno.py",
                17,
                "Hex High Entropy String",
            )
            wrong_detector = SecretFinding(
                finding.path,
                finding.line_number,
                "Secret Keyword",
            )

            self.assertFalse(_is_adjudicated_checksum(snapshot_root, finding))
            self.assertFalse(_is_adjudicated_checksum(snapshot_root, wrong_detector))

    def test_history_scan_fails_redacted_for_credential_fixture(self) -> None:
        candidate = "".join(("synthetic", "-private-", "material-", "A" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            subprocess.run(["git", "init", "--quiet"], cwd=repo_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "audit@example.invalid"],
                cwd=repo_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Audit Fixture"],
                cwd=repo_root,
                check=True,
            )
            repo_root.joinpath("README.md").write_text(
                "benign fixture\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "benign"],
                cwd=repo_root,
                check=True,
            )
            repo_root.joinpath("fixture.py").write_text(
                f'api_key = "{candidate}"\n',
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "credential fixture"],
                cwd=repo_root,
                check=True,
            )

            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        report = "\n".join(render_historical_findings(raised.exception.findings))
        self.assertIn("fixture.py:1", report)
        self.assertNotIn(candidate, report)

    def test_historical_rendering_contains_only_escaped_metadata(self) -> None:
        finding = HistoricalFinding(
            commit="abc\nspoof",
            path="unsafe\nname.py",
            line_number=5,
            detector_type="Detector\rName",
        )
        self.assertEqual(
            render_historical_findings([finding]),
            ["abc\\nspoof unsafe\\nname.py:5 [Detector\\rName]"],
        )

    def test_main_reports_history_tool_failure_categorically(self) -> None:
        sensitive_material = "".join(("synthetic", "-private-", "material"))
        failure = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "archive"],
            stderr=sensitive_material,
        )
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch("scripts.verificar_seguridad.run_secret_scan", return_value=[]),
            patch("scripts.verificar_seguridad.find_personal_paths", return_value=[]),
            patch(
                "scripts.verificar_seguridad.scan_git_history",
                side_effect=failure,
            ),
            patch("scripts.verificar_seguridad.run_dependency_audit") as audit,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = main()

        rendered = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertEqual(stderr.getvalue(), "ERROR_SEGURIDAD: HISTORIAL_GIT\n")
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn(sensitive_material, rendered)
        audit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
