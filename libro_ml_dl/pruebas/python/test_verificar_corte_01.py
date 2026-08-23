import io
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class Corte01VerificationTests(unittest.TestCase):
    def test_reports_corrupt_runtime_before_running_suites(self) -> None:
        from scripts import verificar_corte_01

        with TemporaryDirectory() as directory:
            book_root = Path(directory)
            vendor_dir = book_root / "assets" / "vendor" / "pyodide"
            vendor_dir.mkdir(parents=True)
            (vendor_dir / "pyodide.mjs").touch()
            (vendor_dir / "manifest.local.json").write_text(
                "{}",
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with (
                patch.object(verificar_corte_01, "BOOK_ROOT", book_root),
                patch.object(
                    verificar_corte_01.shutil,
                    "which",
                    side_effect=["/usr/bin/node", "/usr/bin/ruff"],
                ),
                patch.object(
                    verificar_corte_01,
                    "validate_existing_runtime",
                    side_effect=RuntimeError("Runtime corrupto o incompleto"),
                ) as validate_runtime,
                patch.object(verificar_corte_01, "run") as run,
                redirect_stderr(stderr),
            ):
                result = verificar_corte_01.main()

        self.assertEqual(result, 1)
        self.assertIn("Runtime corrupto o incompleto", stderr.getvalue())
        validate_runtime.assert_called_once_with(vendor_dir)
        run.assert_not_called()
