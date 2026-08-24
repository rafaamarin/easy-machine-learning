from __future__ import annotations

import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from scripts.verificar_seguridad import REPO_ROOT as SECURITY_REPO_ROOT
from scripts.verificar_seguridad import (
    HistoricalFinding,
    HistoricalScanError,
    SecretFinding,
    _candidate_files,
    _is_adjudicated_checksum,
    _materialize_commit,
    _parse_git_tree_entries,
    find_personal_paths,
    main,
    parse_secret_results,
    render_historical_findings,
    render_secret_findings,
    run_dependency_audit,
    run_secret_scan,
    scan_git_history,
    scan_git_index,
    scan_security_snapshot,
)


class SecurityVerificationTests(unittest.TestCase):
    @staticmethod
    def _initialize_git_repo(repo_root: Path) -> None:
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

    @staticmethod
    def _commit_all(repo_root: Path, message: str) -> None:
        subprocess.run(["git", "add", "--all"], cwd=repo_root, check=True)
        subprocess.run(
            ["git", "commit", "--quiet", "-m", message],
            cwd=repo_root,
            check=True,
        )

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

    def test_personal_path_in_non_utf8_blob_is_found_everywhere(self) -> None:
        private_marker = "/".join(("", "Users", "rafa", "Documents"))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / "binary.dat"
            fixture.write_bytes(b"\xff\n" + private_marker.encode("ascii") + b"\n")
            self._commit_all(repo_root, "binary personal path")

            current_result = scan_security_snapshot(repo_root)
            index_result = scan_git_index(repo_root)
            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        self.assertEqual(
            [
                (finding.path, finding.line_number)
                for finding in current_result.personal_findings
            ],
            [("binary.dat", 2)],
        )
        self.assertEqual(
            [
                (finding.path, finding.line_number)
                for finding in index_result.personal_findings
            ],
            [("binary.dat", 2)],
        )
        report = "\n".join(render_historical_findings(raised.exception.findings))
        self.assertIn("binary.dat:2", report)
        self.assertNotIn(private_marker, report)

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
                run.return_value = subprocess.CompletedProcess(
                    ["detect-secrets", "scan"],
                    0,
                    stdout=json.dumps(payload),
                    stderr="",
                )
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
                    "scripts.verificar_seguridad.scan_security_snapshot",
                    return_value=SimpleNamespace(
                        rejected=(),
                        adjudicated=(),
                        personal_findings=(),
                    ),
                ),
                patch(
                    "scripts.verificar_seguridad.find_personal_paths",
                    return_value=[],
                ),
                patch(
                    "scripts.verificar_seguridad.scan_git_index",
                    return_value=SimpleNamespace(
                        rejected=(),
                        adjudicated=(),
                        personal_findings=(),
                    ),
                ),
                patch(
                    "scripts.verificar_seguridad.scan_git_history",
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

    def test_snapshot_scan_runs_the_only_allowlisted_pass(self) -> None:
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            repo_root.joinpath("ordinary.txt").write_text(
                'note = "# pragma: allowlist secret"\n',
                encoding="utf-8",
            )
            scanner_commands: list[list[str]] = []

            def scan_without_findings(
                command: list[str],
                **_kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
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
                    "scripts.verificar_seguridad.subprocess.run",
                    side_effect=scan_without_findings,
                ),
            ):
                result = scan_security_snapshot(
                    repo_root,
                    [repo_root / "ordinary.txt"],
                )

        self.assertEqual(result.rejected, ())
        self.assertEqual(result.adjudicated, ())
        self.assertEqual(len(scanner_commands), 2)
        self.assertNotIn("--only-allowlisted", scanner_commands[0])
        self.assertIn("--only-allowlisted", scanner_commands[1])

    def test_current_allowlisted_secret_is_rejected_and_redacted(self) -> None:
        candidate = "".join(("synthetic", "-private-", "value-", "D" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            fixture = repo_root / "fixture.py"
            fixture.write_text(
                f'api_key = "{candidate}"  # pragma: allowlist secret\n',
                encoding="utf-8",
            )

            result = scan_security_snapshot(repo_root, [fixture])

        report = "\n".join(render_secret_findings(list(result.rejected)))
        self.assertIn("fixture.py:1", report)
        self.assertNotIn(candidate, report)
        self.assertEqual(result.adjudicated, ())

    def test_non_utf8_allowlisted_secret_is_rejected_everywhere(self) -> None:
        candidate = "".join(("synthetic", "-private-", "value-", "G" * 32))
        suppressed_line = (
            f'api_key = "{candidate}"  # pragma: allowlist secret\n'.encode()
        )
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / "binary_secret.dat"
            fixture.write_bytes(b"\xff\n" + suppressed_line)
            self._commit_all(repo_root, "binary suppressed secret")

            current_result = scan_security_snapshot(repo_root)
            index_result = scan_git_index(repo_root)
            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        for findings in (current_result.rejected, index_result.rejected):
            report = "\n".join(render_secret_findings(list(findings)))
            self.assertIn("binary_secret.dat:2", report)
            self.assertNotIn(candidate, report)
        historical_report = "\n".join(
            render_historical_findings(raised.exception.findings)
        )
        self.assertIn("binary_secret.dat:2", historical_report)
        self.assertNotIn(candidate, historical_report)

    def test_current_approved_suppressions_are_exactly_adjudicated(self) -> None:
        result = scan_security_snapshot(SECURITY_REPO_ROOT)

        self.assertEqual(result.rejected, ())
        self.assertEqual(len(result.adjudicated), 26)
        self.assertEqual(
            len(
                {(finding.path, finding.line_number) for finding in result.adjudicated}
            ),
            26,
        )

    def test_staged_secret_is_scanned_when_worktree_copy_is_safe(self) -> None:
        candidate = "".join(("synthetic", "-private-", "value-", "E" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / "fixture.py"
            fixture.write_text("value = 'safe'\n", encoding="utf-8")
            self._commit_all(repo_root, "safe")
            fixture.write_text(f'api_key = "{candidate}"\n', encoding="utf-8")
            subprocess.run(["git", "add", "fixture.py"], cwd=repo_root, check=True)
            fixture.write_text("value = 'safe again'\n", encoding="utf-8")

            worktree_result = scan_security_snapshot(repo_root)
            index_result = scan_git_index(repo_root)

        self.assertEqual(worktree_result.rejected, ())
        report = "\n".join(render_secret_findings(list(index_result.rejected)))
        self.assertIn("fixture.py:1", report)
        self.assertNotIn(candidate, report)

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

    def test_current_allowlisted_checksum_lines_are_exactly_adjudicated(
        self,
    ) -> None:
        for path, line_number in (
            ("libro_ml_dl/scripts/preparar_entorno.py", 17),
            ("libro_ml_dl/pruebas/python/test_preparar_entorno.py", 81),
        ):
            finding = SecretFinding(
                path,
                line_number,
                "Hex High Entropy String",
            )
            self.assertTrue(_is_adjudicated_checksum(SECURITY_REPO_ROOT, finding))

    def test_git_tree_parser_accepts_only_unique_regular_utf8_blobs(self) -> None:
        object_id = b"a" * 40
        valid_inventory = (
            b"100644 blob " + object_id + b"\tfile.txt\0"
            b"100755 blob " + object_id + b"\tscript.sh\0"
        )
        self.assertEqual(len(_parse_git_tree_entries(valid_inventory)), 2)

        invalid_inventories = (
            b"120000 blob " + object_id + b"\tlink\0",
            b"160000 commit " + object_id + b"\tsubmodule\0",
            b"100644 blob " + object_id + b"\tduplicate\0"
            b"100644 blob " + object_id + b"\tduplicate\0",
            b"100644 blob " + object_id + b"\tConfig.py\0"
            b"100644 blob " + object_id + b"\tconfig.py\0",
            b"100644 blob " + object_id + b"\tcaf\xc3\xa9.py\0"
            b"100644 blob " + object_id + b"\tcafe\xcc\x81.py\0",
            b"100644 blob " + object_id + b"\tinvalid-\xff-name\0",
            b"100644 blob " + object_id + b"\t../escaped\0",
            b"100600 blob " + object_id + b"\tunsupported-mode\0",
        )
        for inventory in invalid_inventories:
            with self.subTest(inventory=inventory[:16]):
                with self.assertRaises(RuntimeError):
                    _parse_git_tree_entries(inventory)

    def test_colliding_git_paths_fail_before_any_blob_is_read(self) -> None:
        object_id = b"a" * 40
        inventory = subprocess.CompletedProcess(
            ["git", "ls-tree"],
            0,
            stdout=(
                b"100644 blob " + object_id + b"\tConfig.py\0"
                b"100644 blob " + object_id + b"\tconfig.py\0"
            ),
            stderr=b"",
        )
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            snapshot_root = repo_root / "snapshot"
            snapshot_root.mkdir()
            with patch(
                "scripts.verificar_seguridad.subprocess.run",
                return_value=inventory,
            ) as run:
                with self.assertRaisesRegex(RuntimeError, "colisión"):
                    _materialize_commit(repo_root, "a" * 40, snapshot_root)

        self.assertEqual(run.call_count, 1)

    def test_history_scans_tracked_files_in_normally_excluded_paths(self) -> None:
        candidate = "".join(("synthetic", "-private-", "material-", "B" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / ".superpowers" / "reviewer_fixture.py"
            fixture.parent.mkdir(parents=True)
            fixture.write_text(f'api_key = "{candidate}"\n', encoding="utf-8")
            self._commit_all(repo_root, "tracked excluded path")

            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        report = "\n".join(render_historical_findings(raised.exception.findings))
        self.assertIn(".superpowers/reviewer_fixture.py:1", report)
        self.assertNotIn(candidate, report)

    def test_history_ignores_export_ignore_and_scans_every_blob(self) -> None:
        candidate = "".join(("synthetic", "-private-", "material-", "C" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            repo_root.joinpath(".gitattributes").write_text(
                "hidden.py export-ignore\n",
                encoding="utf-8",
            )
            repo_root.joinpath("hidden.py").write_text(
                f'api_key = "{candidate}"\n',
                encoding="utf-8",
            )
            self._commit_all(repo_root, "export ignored credential")

            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        report = "\n".join(render_historical_findings(raised.exception.findings))
        self.assertIn("hidden.py:1", report)
        self.assertNotIn(candidate, report)

    def test_checksum_line_with_second_entropy_literal_is_rejected(self) -> None:
        approved_core = "".join(
            (
                "f528dcce",
                "a95fa8ec",
                "54295fd6",
                "5bf86dd6",
                "1183d11f",
                "0e52563d",
                "c8eadda4",
                "5e0f78d6",
            )
        )
        second_value = "".join(("01234567", "89abcdef") * 4)
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / "libro_ml_dl/scripts/preparar_entorno.py"
            fixture.parent.mkdir(parents=True)
            source_lines = ["" for _ in range(16)]
            source_lines.append(
                f'CORE_SHA256 = "{approved_core}"; OTHER = "{second_value}"'
            )
            fixture.write_text("\n".join(source_lines), encoding="utf-8")
            self._commit_all(repo_root, "ambiguous checksum line")

            with self.assertRaises(HistoricalScanError) as raised:
                scan_git_history(repo_root)

        report = "\n".join(render_historical_findings(raised.exception.findings))
        self.assertIn("libro_ml_dl/scripts/preparar_entorno.py:17", report)
        self.assertNotIn(approved_core, report)
        self.assertNotIn(second_value, report)

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

    def test_history_scan_rejects_allowlisted_credential_fixture(self) -> None:
        candidate = "".join(("synthetic", "-private-", "value-", "F" * 32))
        with TemporaryDirectory() as directory:
            repo_root = Path(directory)
            self._initialize_git_repo(repo_root)
            fixture = repo_root / "fixture.py"
            fixture.write_text(
                f'api_key = "{candidate}"  # pragma: allowlist secret\n',
                encoding="utf-8",
            )
            self._commit_all(repo_root, "suppressed credential")

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
            patch(
                "scripts.verificar_seguridad.scan_security_snapshot",
                return_value=SimpleNamespace(
                    rejected=(),
                    adjudicated=(),
                    personal_findings=(),
                ),
            ),
            patch("scripts.verificar_seguridad.find_personal_paths", return_value=[]),
            patch(
                "scripts.verificar_seguridad.scan_git_index",
                return_value=SimpleNamespace(
                    rejected=(),
                    adjudicated=(),
                    personal_findings=(),
                ),
            ),
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

    def test_main_escapes_controls_in_personal_path_metadata(self) -> None:
        unsafe_path = SECURITY_REPO_ROOT / "unsafe\nname.txt"
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch(
                "scripts.verificar_seguridad.scan_security_snapshot",
                return_value=SimpleNamespace(
                    rejected=(),
                    adjudicated=(),
                    personal_findings=(
                        SecretFinding(
                            "unsafe\nname.txt",
                            1,
                            "Ruta personal",
                        ),
                    ),
                ),
            ),
            patch(
                "scripts.verificar_seguridad.find_personal_paths",
                return_value=[unsafe_path],
            ),
            patch(
                "scripts.verificar_seguridad.scan_git_index",
                return_value=SimpleNamespace(
                    rejected=(),
                    adjudicated=(),
                    personal_findings=(),
                ),
            ),
            patch("scripts.verificar_seguridad.scan_git_history", return_value=[]),
            patch("scripts.verificar_seguridad.run_dependency_audit") as audit,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = main()

        self.assertEqual(result, 1)
        self.assertEqual(stderr.getvalue(), "RUTA_PERSONAL: unsafe\\nname.txt\n")
        self.assertEqual(stdout.getvalue(), "")
        audit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
