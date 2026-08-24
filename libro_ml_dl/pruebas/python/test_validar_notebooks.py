from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import nbformat
from nbclient.exceptions import CellExecutionError

from scripts.validar_notebooks import execute_notebook, project_kernel_path


class NotebookExecutionTests(unittest.TestCase):
    def _write_notebook(self, root: Path, source: str) -> Path:
        notebook_path = root / "demo.ipynb"
        notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)])
        nbformat.write(notebook, notebook_path)
        return notebook_path

    def test_executes_with_the_current_project_interpreter(self) -> None:
        with TemporaryDirectory() as directory:
            path = self._write_notebook(
                Path(directory),
                "import sys\nassert sys.version_info >= (3, 11)\n2 + 2",
            )
            summary = execute_notebook(path)
        self.assertEqual(summary.code_cells, 1)
        self.assertEqual(summary.error_outputs, 0)

    def test_execution_does_not_rewrite_source_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            path = self._write_notebook(Path(directory), "value = 42")
            original = path.read_bytes()
            execute_notebook(path)
            self.assertEqual(path.read_bytes(), original)

    def test_cell_errors_are_not_hidden(self) -> None:
        with TemporaryDirectory() as directory:
            path = self._write_notebook(
                Path(directory),
                "raise RuntimeError('fallo reproducible')",
            )
            with self.assertRaises(CellExecutionError):
                execute_notebook(path)

    def test_relative_writes_cannot_modify_source_siblings(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sibling = root / "sibling.txt"
            sibling.write_text("original", encoding="utf-8")
            path = self._write_notebook(
                root,
                "from pathlib import Path\n"
                "Path('sibling.txt').write_text('changed', encoding='utf-8')",
            )
            execute_notebook(path)

            self.assertEqual(sibling.read_text(encoding="utf-8"), "original")

    def test_relative_self_mutation_changes_only_disposable_copy(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_notebook(
                root,
                "from pathlib import Path\n"
                "Path('demo.ipynb').write_text('mutated', encoding='utf-8')",
            )
            original = path.read_bytes()

            summary = execute_notebook(path)

            self.assertEqual(summary.path, path)
            self.assertEqual(path.read_bytes(), original)

    def test_concurrent_source_edit_is_preserved_when_execution_fails(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._write_notebook(root, "pass")
            original = path.read_bytes()
            concurrent_bytes = b"concurrent notebook edit\n"

            def edit_source_then_fail() -> None:
                path.write_bytes(concurrent_bytes)
                raise RuntimeError("fallo de ejecución sintético")

            with patch(
                "scripts.validar_notebooks.NotebookClient.execute",
                side_effect=edit_source_then_fail,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "notebook fuente",
                ) as raised:
                    execute_notebook(path)

            self.assertNotEqual(path.read_bytes(), original)
            self.assertEqual(path.read_bytes(), concurrent_bytes)
            self.assertIsInstance(raised.exception.__context__, RuntimeError)

    def test_project_kernel_path_restores_previous_value_after_error(self) -> None:
        with patch.dict(os.environ, {"JUPYTER_PATH": "previous"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with project_kernel_path():
                    self.assertNotEqual(os.environ["JUPYTER_PATH"], "previous")
                    raise RuntimeError("synthetic failure")
            self.assertEqual(os.environ["JUPYTER_PATH"], "previous")

    def test_project_kernel_path_removes_temporary_value_after_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with project_kernel_path():
                    self.assertIn("JUPYTER_PATH", os.environ)
                    raise RuntimeError("synthetic failure")
            self.assertNotIn("JUPYTER_PATH", os.environ)


if __name__ == "__main__":
    unittest.main()
