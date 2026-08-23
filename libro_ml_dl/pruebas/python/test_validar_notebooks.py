from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from nbclient.exceptions import CellExecutionError

from scripts.validar_notebooks import execute_notebook


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


if __name__ == "__main__":
    unittest.main()
