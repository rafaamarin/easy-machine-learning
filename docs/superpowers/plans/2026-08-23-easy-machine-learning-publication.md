# Easy Machine Learning Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, secure, validate, brand, and publish `rafaamarin/easy-machine-learning` as a private, reproducible repository containing the interactive book and its three cited notebooks.

**Architecture:** Start from the approved clean repository and import only the 47 tracked book files from commit `d9d044f3892bf636d83f47001cb3a8fb7f41e9a0`, plus three byte-identical notebooks. Keep the book in `libro_ml_dl/`, expose simple root wrappers, validate notebooks in isolated temporary kernels, and make the private GitHub push the final operation after code review and security gates.

**Tech Stack:** Python 3.11+, `uv`, HTML/CSS/JavaScript, Pyodide 314.0.5, JupyterLab, `nbclient`, Node.js 22, Ruff, `detect-secrets` 1.5.0, `pip-audit` 2.10.1, GitHub Actions, GitHub CLI.

**Spec:** `docs/superpowers/specs/2026-08-23-easy-machine-learning-publication-design.md`

## Global Constraints

- Work only in the new repository root. Treat the locations supplied through
  `easy_ml_vault_source` and `easy_ml_book_source` as read-only sources; never
  write either value into a committed file.
- Never modify any source `.ipynb`; validate execution in memory or in disposable copies.
- Never permanently delete files or directories; use `/usr/bin/trash` for local cleanup.
- Keep the GitHub repository private; changing visibility requires a later explicit user request.
- Do not print, commit, or push any real credential. A real secret stops publication and must be rotated.
- Include exactly the book plus the three approved notebooks; do not import the remaining UNIR vault or its Git history.
- Preserve notebook bytes and verify the approved SHA-256 values after every copy.
- Support macOS and Linux natively and Windows through WSL; do not add native Windows process control.
- Require Python 3.11+; lock Python packages with `uv.lock`; do not install global Jupyter kernels.
- Bind web and Jupyter services only to `127.0.0.1`.
- Do not version `.venv`, caches, `configuracion/local.json`, or downloaded Pyodide files.
- License code under MIT and educational text, notebooks, and visual assets under CC BY 4.0.
- Use snake_case for Python variables, functions, scripts, and test names; follow PEP 8 and practical type hints.
- Implement behavioral changes with red-green-refactor TDD and commit each task independently.
- Before the remote is created, require zero Critical/Important review findings, a clean worktree, a green functional gate, a green notebook gate, a clean secret scan, and a clean dependency audit.

---

### Task 1: Import the approved book and source notebooks

**Files:**
- Create: `.gitignore`
- Create: `libro_ml_dl/**` from the approved 47-file Git tree
- Create: `material_fuente/notebooks/01-series-dataframes.ipynb`
- Create: `material_fuente/notebooks/07-estadisticas-basicas.ipynb`
- Create: `material_fuente/notebooks/05-scale.ipynb`
- Create: `pruebas_publicacion/test_material_fuente.py`
- Modify: `libro_ml_dl/contenido_fuente/mapa_fuentes.json`

**Interfaces:**
- Consumes: source commit `d9d044f3892bf636d83f47001cb3a8fb7f41e9a0`
  and three approved notebook paths below the directory supplied at execution
  time through `easy_ml_vault_source`.
- Produces: an import initially identical to book tree
  `2363fbea93bb7d6ec3c06bd7fe68b6855194f9e3`, followed only by the explicit
  publication changes in this plan, plus byte-identical source notebooks
  addressable from the book root's parent.

- [ ] **Step 1: Write the failing provenance test**

Create `pruebas_publicacion/test_material_fuente.py`:

```python
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "material_fuente/notebooks/01-series-dataframes.ipynb": (
        "15f0a0f4137ba81117f8bacf90dbd341"  # pragma: allowlist secret
        "828335963191b2fdc3a213650df510ea"  # pragma: allowlist secret
    ),
    "material_fuente/notebooks/07-estadisticas-basicas.ipynb": (
        "f4352008a8f973f496dba58c08740b25"  # pragma: allowlist secret
        "0daac81b20b94ba3b1eac86b2221e30a"  # pragma: allowlist secret
    ),
    "material_fuente/notebooks/05-scale.ipynb": (
        "894a588d2eb24d02d032ac61a2f2961e"  # pragma: allowlist secret
        "ef1920a9c6cfdb17e50948d0612dbeaf"  # pragma: allowlist secret
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceMaterialTests(unittest.TestCase):
    def test_notebooks_are_byte_identical_to_approved_sources(self) -> None:
        for relative_path, expected_hash in EXPECTED_HASHES.items():
            self.assertEqual(sha256_file(REPO_ROOT / relative_path), expected_hash)

    def test_source_map_uses_repository_relative_notebook_paths(self) -> None:
        source_map_path = (
            REPO_ROOT / "libro_ml_dl/contenido_fuente/mapa_fuentes.json"
        )
        source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
        sources = source_map["modules"]["01_datos_y_formas"]["sources"]
        self.assertEqual(
            sources,
            [
                "material_fuente/notebooks/01-series-dataframes.ipynb",
                "material_fuente/notebooks/07-estadisticas-basicas.ipynb",
                "material_fuente/notebooks/05-scale.ipynb",
            ],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the missing snapshot fails**

Run:

```bash
python3 -m unittest pruebas_publicacion/test_material_fuente.py -v
```

Expected: `ERROR` or `FAIL` because `libro_ml_dl/` and the three notebooks are absent.

- [ ] **Step 3: Import only the approved Git tree**

Run from the repository root:

```bash
test -d "${easy_ml_book_source:?set easy_ml_book_source locally}"
git -C "$easy_ml_book_source" \
  archive d9d044f3892bf636d83f47001cb3a8fb7f41e9a0 libro_ml_dl \
  | tar -x -C .
```

Confirm the imported tree contains exactly 47 tracked source files:

```bash
find libro_ml_dl -type f | wc -l
```

Expected: `47` before any new tests or local environment files are added.

- [ ] **Step 4: Copy the three approved notebooks without transforming them**

Run:

```bash
test -d "${easy_ml_vault_source:?set easy_ml_vault_source locally}"
mkdir -p material_fuente/notebooks
cp "$easy_ml_vault_source/01-machine-learning/01-sesiones/03-analisis-datos/01-series-dataframes.ipynb" \
  material_fuente/notebooks/01-series-dataframes.ipynb
cp "$easy_ml_vault_source/01-machine-learning/01-sesiones/03-analisis-datos/07-estadisticas-basicas.ipynb" \
  material_fuente/notebooks/07-estadisticas-basicas.ipynb
cp "$easy_ml_vault_source/01-machine-learning/01-sesiones/05-modelado-datos/05-pipelines-y-preprocesados/05-scale.ipynb" \
  material_fuente/notebooks/05-scale.ipynb
```

Do not clear outputs, normalize metadata, or reserialize the notebook JSON.

- [ ] **Step 5: Point provenance at the new repository-relative paths**

Replace the `sources` list for `01_datos_y_formas` in
`libro_ml_dl/contenido_fuente/mapa_fuentes.json` with:

```json
[
  "material_fuente/notebooks/01-series-dataframes.ipynb",
  "material_fuente/notebooks/07-estadisticas-basicas.ipynb",
  "material_fuente/notebooks/05-scale.ipynb"
]
```

Because `resolve_vault_root()` defaults to `book_root.parent`, these paths resolve
inside the new repository without machine-local configuration.

- [ ] **Step 6: Establish root ignore boundaries**

Create `.gitignore`:

```gitignore
.DS_Store
**/.DS_Store
**/.venv/
**/.ruff_cache/
**/__pycache__/
**/*.pyc
libro_ml_dl/configuracion/local.json
libro_ml_dl/assets/vendor/pyodide/*
!libro_ml_dl/assets/vendor/pyodide/.gitkeep
```

- [ ] **Step 7: Run provenance and existing static validation**

Run:

```bash
python3 -m unittest pruebas_publicacion/test_material_fuente.py -v
cd libro_ml_dl
uv sync --locked --group validation
uv run python scripts/validar_contenido.py
uv run python scripts/construir_contenido.py --check
```

Expected: 2 provenance tests pass, followed by `VALIDACION_ESTATICA_OK` and
`HTML_GENERADO_AL_DIA`.

- [ ] **Step 8: Confirm source repositories were not changed**

Run:

```bash
git -C "$easy_ml_vault_source" diff -- \
  '01-machine-learning/01-sesiones/03-analisis-datos/01-series-dataframes.ipynb' \
  '01-machine-learning/01-sesiones/03-analisis-datos/07-estadisticas-basicas.ipynb' \
  '01-machine-learning/01-sesiones/05-modelado-datos/05-pipelines-y-preprocesados/05-scale.ipynb'
git -C "$easy_ml_book_source" status --short
```

Expected: no new diff attributable to this task; the source worktree remains on
`d9d044f3892bf636d83f47001cb3a8fb7f41e9a0` with no tracked modifications.

- [ ] **Step 9: Commit the clean import**

```bash
git add .gitignore libro_ml_dl material_fuente pruebas_publicacion
git commit -m "feat: import interactive book and source notebooks"
```

---

### Task 2: Close the three pre-publication code findings

**Files:**
- Modify: `libro_ml_dl/assets/js/pyodide_cliente.mjs`
- Modify: `libro_ml_dl/assets/js/app.mjs`
- Modify: `libro_ml_dl/assets/js/jupyter_url.mjs`
- Modify: `libro_ml_dl/scripts/validar_contenido.py`
- Modify: `libro_ml_dl/pruebas/js/pyodide_cliente.test.mjs`
- Modify: `libro_ml_dl/pruebas/js/jupyter_url.test.mjs`
- Modify: `libro_ml_dl/pruebas/python/test_contenido_modulo_01.py`

**Interfaces:**
- Consumes: `PyodideSession`, `validate_jupyter_url()`, `resolve_book_path()`, and `validate_learning_source()` from Task 1's imported snapshot.
- Produces: `consume_jupyter_url(search: string, stored_value: string | null)` and `validate_available_learning_sources(manifest: dict, book_root: Path) -> list[str]`; guarantees worker cleanup precedes callbacks.

- [ ] **Step 1: Add failing worker reentrancy regressions**

Append to `libro_ml_dl/pruebas/js/pyodide_cliente.test.mjs`:

```javascript
test("invalidates a failed worker before notifying subscribers", async () => {
  const workers = [];
  const session = new PyodideSession({
    worker_factory: () => {
      const worker = new FakeWorker();
      workers.push(worker);
      return worker;
    },
    worker_url: "worker.mjs",
  });
  let retry;
  session.subscribe((message) => {
    if (message.type === "error") {
      retry = session.run("retry", "2 + 2", []);
    }
  });

  const first = session.run("first", "1 + 1", []);
  workers[0].emit_error("bootstrap failure");

  await assert.rejects(first, /bootstrap failure/);
  assert.equal(workers[0].terminated, true);
  assert.equal(workers.length, 2);
  const request_id = workers[1].messages[0].request_id;
  workers[1].emit({
    type: "result",
    request_id,
    lab_id: "retry",
    payload: { value: "4" },
  });
  assert.deepEqual(await retry, { value: "4" });
});

test("listener exceptions cannot prevent failed-worker cleanup", async () => {
  const worker = new FakeWorker();
  const session = new PyodideSession({
    worker_factory: () => worker,
    worker_url: "worker.mjs",
  });
  session.subscribe(() => {
    throw new Error("listener failure");
  });

  const pending = session.run("demo", "1 + 1", []);
  assert.throws(() => worker.emit_error("bootstrap failure"), /listener failure/);
  await assert.rejects(pending, /bootstrap failure/);
  assert.equal(worker.terminated, true);
  assert.equal(session.worker, null);
});
```

- [ ] **Step 2: Add failing validator and empty-query regressions**

Add this import to `test_contenido_modulo_01.py`:

```python
from unittest.mock import patch
```

Add the test:

```python
def test_skips_pedagogical_read_for_source_outside_book(self) -> None:
    manifest = {
        "modules": [
            {
                "id": "escaped",
                "status": "disponible",
                "source": "../outside.md",
            }
        ]
    }
    with TemporaryDirectory() as temporary_directory:
        book_root = Path(temporary_directory) / "libro_ml_dl"
        book_root.mkdir()
        with patch.object(
            validar_contenido,
            "validate_learning_source",
            side_effect=AssertionError("unsafe read"),
        ) as validator:
            errors = validar_contenido.validate_available_learning_sources(
                manifest,
                book_root,
            )
    self.assertEqual(errors, [])
    validator.assert_not_called()
```

Append to `libro_ml_dl/pruebas/js/jupyter_url.test.mjs`:

```javascript
import {
  consume_jupyter_url,
  validate_jupyter_url,
} from "../../assets/js/jupyter_url.mjs";

test("an explicitly empty query clears the stored Jupyter URL", () => {
  assert.deepEqual(
    consume_jupyter_url(
      "?jupyter_url=",
      "http://127.0.0.1:8888/lab?token=old",
    ),
    { value: null, clean_query: true },
  );
});

test("an absent query reuses only a valid stored Jupyter URL", () => {
  assert.deepEqual(
    consume_jupyter_url("", "http://127.0.0.1:8888/lab?token=stored"),
    {
      value: "http://127.0.0.1:8888/lab?token=stored",
      clean_query: false,
    },
  );
});
```

Replace the original single-function import in that test file rather than
declaring `validate_jupyter_url` twice.

- [ ] **Step 3: Run focal tests and verify all three defects fail**

Run:

```bash
cd libro_ml_dl
node --test pruebas/js/pyodide_cliente.test.mjs pruebas/js/jupyter_url.test.mjs
uv run --group validation python -m unittest \
  pruebas/python/test_contenido_modulo_01.py -v
```

Expected: worker reentrancy fails because no second worker is created; the JS
module lacks `consume_jupyter_url`; Python lacks
`validate_available_learning_sources`.

- [ ] **Step 4: Invalidate the worker before any externally controlled callback**

In the worker `error` callback in `pyodide_cliente.mjs`, use this order:

```javascript
const message = event.message || "No se pudo iniciar Pyodide";
const failed_pending = this.pending;
const lab_id = failed_pending?.lab_id ?? "";
this.pending = null;
this.worker = null;
worker.terminate();
if (failed_pending) failed_pending.reject(new Error(message));
for (const listener of this.listeners) {
  listener({
    type: "error",
    request_id: 0,
    lab_id,
    payload: { message, traceback: "" },
  });
}
```

Keep the existing `if (worker !== this.worker) return` identity guard before
capturing state. Do not recreate a worker inside the error callback; `run()`
remains the only lazy recovery path.

- [ ] **Step 5: Add a pure Jupyter query consumer and use it in the app**

Append to `jupyter_url.mjs`:

```javascript
export function consume_jupyter_url(search, stored_value) {
  const query = new URLSearchParams(search);
  if (query.has("jupyter_url")) {
    return {
      value: validate_jupyter_url(query.get("jupyter_url")),
      clean_query: true,
    };
  }
  return {
    value: validate_jupyter_url(stored_value),
    clean_query: false,
  };
}
```

Replace `app.mjs` lines that directly inspect `URLSearchParams` with:

```javascript
const jupyter_selection = consume_jupyter_url(
  window.location.search,
  sessionStorage.getItem("libro_ml_dl_jupyter_url"),
);
if (jupyter_selection.value) {
  sessionStorage.setItem(
    "libro_ml_dl_jupyter_url",
    jupyter_selection.value,
  );
} else {
  sessionStorage.removeItem("libro_ml_dl_jupyter_url");
}
if (jupyter_selection.clean_query) {
  history.replaceState({}, "", window.location.pathname + window.location.hash);
}
```

Import both `consume_jupyter_url` and `validate_jupyter_url` only if the latter
remains directly used; otherwise remove the unused import. Set the anchor from
`jupyter_selection.value`.

- [ ] **Step 6: Confine every pedagogical source read**

Import `resolve_book_path` in both import branches of `validar_contenido.py` and
add:

```python
def validate_available_learning_sources(
    manifest: dict[str, object],
    book_root: Path,
) -> list[str]:
    errors: list[str] = []
    modules = manifest.get("modules", [])
    if not isinstance(modules, list):
        return errors
    for module in modules:
        if not isinstance(module, dict) or module.get("status") != "disponible":
            continue
        source = module.get("source")
        if not isinstance(source, str):
            continue
        try:
            source_path = resolve_book_path(book_root, source)
        except ValueError:
            continue
        module_id = module.get("id")
        required_markers = (
            PEDAGOGICAL_MARKERS
            if module_id == "01_datos_y_formas"
            else {"reto", "observa", "modifica", "comprueba"}
        )
        errors.extend(
            validate_learning_source(source_path, required_markers, book_root)
        )
    return errors
```

Replace the raw loop in `main()` with:

```python
errors.extend(validate_available_learning_sources(manifest, book_root))
```

`validate_manifest()` remains responsible for reporting the rejected path;
this helper independently guarantees that it is never opened.

- [ ] **Step 7: Run focal and complete non-runtime suites**

```bash
cd libro_ml_dl
node --test pruebas/js/*.test.mjs
uv run --group validation python -m unittest discover \
  -s pruebas/python -p 'test_*.py' -v
uv run --group validation ruff check scripts pruebas contenido_fuente
uv run --group validation ruff format --check scripts pruebas contenido_fuente
uv run python scripts/validar_contenido.py
uv run python scripts/construir_contenido.py --check
```

Expected: all tests and static checks pass. Run `git diff --check` from the
repository root.

- [ ] **Step 8: Commit the blocking fixes**

```bash
git add libro_ml_dl/assets/js libro_ml_dl/scripts/validar_contenido.py \
  libro_ml_dl/pruebas
git commit -m "fix: close runtime and content security boundaries"
```

---

### Task 3: Provide portable project-local installation and root commands

**Files:**
- Create: `instalar.sh`
- Create: `lanzar.sh`
- Create: `verificar.sh`
- Create: `libro_ml_dl/.python-version`
- Create: `pruebas_publicacion/test_comandos_raiz.py`
- Modify: `libro_ml_dl/pyproject.toml`
- Modify: `libro_ml_dl/uv.lock`
- Modify: `libro_ml_dl/scripts/lanzar.py`
- Modify: `libro_ml_dl/pruebas/python/test_lanzar.py`

**Interfaces:**
- Consumes: `scripts/preparar_entorno.py --yes`, `scripts/lanzar.py`, and `scripts/verificar_corte_01.py`.
- Produces: root commands `./instalar.sh [--yes]`, `./lanzar.sh [launcher args]`, and `./verificar.sh`; a locked `notebooks` group and `security` group.

- [ ] **Step 1: Write failing wrapper and public-kernel tests**

Create `pruebas_publicacion/test_comandos_raiz.py`:

```python
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
```

Append to `test_lanzar.py`:

```python
def test_launcher_copy_has_no_unir_specific_kernel_names(self) -> None:
    source = (BOOK_ROOT / "scripts/lanzar.py").read_text(encoding="utf-8")
    self.assertNotIn("unir-tf", source)
    self.assertNotIn("unir-torch", source)
```

- [ ] **Step 2: Run tests and verify the public wrappers are absent**

```bash
python3 -m unittest pruebas_publicacion/test_comandos_raiz.py -v
cd libro_ml_dl
uv run --group validation python -m unittest pruebas/python/test_lanzar.py -v
```

Expected: root-command tests fail because files are missing; launcher test fails
because the imported copy still names UNIR kernels.

- [ ] **Step 3: Add locked notebook and security dependency groups**

Add to `libro_ml_dl/pyproject.toml`:

```toml
notebooks = [
    "ipykernel>=6.30,<8",
    "jupyterlab>=4.4,<5",
    "matplotlib==3.10.8",
    "nbclient>=0.10,<1",
    "nbformat>=5.10,<6",
    "numpy==2.4.6",
    "pandas==3.0.2",
    "scikit-learn==1.8.0",
]
security = [
    "detect-secrets==1.5.0",
    "pip-audit==2.10.1",
]
```

Keep these lists under `[dependency-groups]` next to `validation`. Create
`libro_ml_dl/.python-version` containing exactly:

```text
3.11
```

Update the lockfile:

```bash
cd libro_ml_dl
uv lock
uv sync --locked --group validation --group notebooks --group security
```

- [ ] **Step 4: Create the root installation command**

Create executable `instalar.sh`:

```sh
#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: instala uv desde https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if ! uv python find '>=3.11' >/dev/null 2>&1; then
  echo "ERROR: se requiere Python 3.11 o posterior." >&2
  exit 1
fi

cd "$book_root"
uv sync --locked --group validation --group notebooks --group security
uv run python scripts/preparar_entorno.py "$@"
```

- [ ] **Step 5: Create root launch and verification commands**

Create executable `lanzar.sh`:

```sh
#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: ejecuta ./instalar.sh después de instalar uv." >&2
  exit 1
fi

cd "$book_root"
exec uv run --locked --group notebooks python scripts/lanzar.py "$@"
```

Create executable `verificar.sh`:

```sh
#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
uv run --locked --group validation --group notebooks \
  python scripts/verificar_corte_01.py
```

Set executable bits:

```bash
chmod +x instalar.sh lanzar.sh verificar.sh
```

- [ ] **Step 6: Replace course-specific kernel messaging**

In `scripts/lanzar.py`, replace the two `unir-tf`/`unir-torch` status blocks with:

```python
names = kernel_names(jupyter)
python_status = "disponible" if "python3" in names else "no registrado"
print(f"Kernel Python del proyecto: {python_status}")
```

Do not install or register a user-global kernelspec. JupyterLab launched from
`.venv` supplies the project interpreter; the status is diagnostic only.

- [ ] **Step 7: Validate scripts, lockfile, launcher, and full unit suite**

```bash
python3 -m unittest pruebas_publicacion/test_comandos_raiz.py -v
sh -n instalar.sh lanzar.sh verificar.sh
cd libro_ml_dl
uv lock --check
uv sync --locked --group validation --group notebooks --group security
uv run --group validation python -m unittest discover \
  -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
uv run --group validation ruff check scripts pruebas contenido_fuente
uv run --group validation ruff format --check scripts pruebas contenido_fuente
```

Expected: all checks pass and `git diff --check` is clean.

- [ ] **Step 8: Commit portable setup**

```bash
git add instalar.sh lanzar.sh verificar.sh pruebas_publicacion \
  libro_ml_dl/.python-version libro_ml_dl/pyproject.toml libro_ml_dl/uv.lock \
  libro_ml_dl/scripts/lanzar.py libro_ml_dl/pruebas/python/test_lanzar.py
git commit -m "feat: add portable local setup and launch commands"
```

---

### Task 4: Execute every cited notebook reproducibly without modifying it

**Files:**
- Create: `libro_ml_dl/scripts/validar_notebooks.py`
- Create: `libro_ml_dl/pruebas/python/test_validar_notebooks.py`
- Modify: `verificar.sh`

**Interfaces:**
- Consumes: the `notebooks` dependency group and the three paths imported in Task 1.
- Produces: `execute_notebook(path: Path) -> NotebookExecutionSummary` and a CLI that exits nonzero on a cell error, kernel failure, or source-byte mutation.

- [ ] **Step 1: Write failing notebook-runner tests**

Create `libro_ml_dl/pruebas/python/test_validar_notebooks.py`:

```python
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
        notebook = nbformat.v4.new_notebook(
            cells=[nbformat.v4.new_code_cell(source)]
        )
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
```

- [ ] **Step 2: Run the focal test and verify the module is missing**

```bash
cd libro_ml_dl
uv run --group notebooks --group validation python -m unittest \
  pruebas/python/test_validar_notebooks.py -v
```

Expected: import error for `scripts.validar_notebooks`.

- [ ] **Step 3: Implement a temporary project-local kernelspec**

Create `libro_ml_dl/scripts/validar_notebooks.py`:

```python
from __future__ import annotations

import hashlib
import json
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

import nbformat
from nbclient import NotebookClient


BOOK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_ROOT.parent
NOTEBOOK_PATHS = (
    REPO_ROOT / "material_fuente/notebooks/01-series-dataframes.ipynb",
    REPO_ROOT / "material_fuente/notebooks/07-estadisticas-basicas.ipynb",
    REPO_ROOT / "material_fuente/notebooks/05-scale.ipynb",
)
KERNEL_NAME = "easy-machine-learning"


@dataclass(frozen=True)
class NotebookExecutionSummary:
    path: Path
    code_cells: int
    error_outputs: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def project_kernel_path() -> Iterator[None]:
    previous_jupyter_path = os.environ.get("JUPYTER_PATH")
    with TemporaryDirectory(prefix="easy_ml_kernel_") as directory:
        kernel_directory = Path(directory) / "kernels" / KERNEL_NAME
        kernel_directory.mkdir(parents=True)
        kernel_directory.joinpath("kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        sys.executable,
                        "-m",
                        "ipykernel_launcher",
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": "Easy Machine Learning",
                    "language": "python",
                }
            ),
            encoding="utf-8",
        )
        os.environ["JUPYTER_PATH"] = directory
        try:
            yield
        finally:
            if previous_jupyter_path is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = previous_jupyter_path


def execute_notebook(path: Path) -> NotebookExecutionSummary:
    original_hash = sha256_file(path)
    notebook = nbformat.read(path, as_version=4)
    with project_kernel_path():
        client = NotebookClient(
            notebook,
            timeout=180,
            kernel_name=KERNEL_NAME,
            resources={"metadata": {"path": str(path.parent)}},
        )
        client.execute()
    if sha256_file(path) != original_hash:
        raise RuntimeError(f"el notebook fuente cambió durante la ejecución: {path}")
    code_cells = sum(cell.cell_type == "code" for cell in notebook.cells)
    error_outputs = sum(
        output.output_type == "error"
        for cell in notebook.cells
        for output in cell.get("outputs", [])
    )
    return NotebookExecutionSummary(path, code_cells, error_outputs)


def main() -> int:
    os.environ.setdefault("MPLBACKEND", "Agg")
    for path in NOTEBOOK_PATHS:
        summary = execute_notebook(path)
        print(
            "NOTEBOOK_OK "
            f"path={summary.path.relative_to(REPO_ROOT)} "
            f"code_cells={summary.code_cells} errors={summary.error_outputs}"
        )
    print("NOTEBOOKS_REPRODUCIBLES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Make the root functional gate complete**

Replace `verificar.sh` with:

```sh
#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
uv run --locked --group validation --group notebooks --group security \
  python -m unittest discover -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
uv run --locked --group validation ruff check scripts pruebas contenido_fuente
uv run --locked --group validation ruff format --check \
  scripts pruebas contenido_fuente
uv run --locked --group validation python scripts/verificar_corte_01.py
uv run --locked --group validation --group notebooks \
  python scripts/validar_notebooks.py

cd "$repo_root"
python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
git diff --check
printf '%s\n' 'VERIFICACION_COMPLETA_OK'
```

This command is the functional/reproducibility gate. Dependency and secret
auditing remain in `./verificar_seguridad.sh` so each failure category is clear.

- [ ] **Step 5: Run the synthetic and real notebook gates**

```bash
cd libro_ml_dl
uv run --group notebooks --group validation python -m unittest \
  pruebas/python/test_validar_notebooks.py -v
uv run --group notebooks python scripts/validar_notebooks.py
cd ..
python3 -m unittest pruebas_publicacion/test_material_fuente.py -v
```

Expected: three synthetic tests pass; each real notebook reports
`NOTEBOOK_OK ... errors=0`; final line is `NOTEBOOKS_REPRODUCIBLES_OK`; approved
SHA-256 values remain unchanged.

- [ ] **Step 6: Run Ruff and the complete unit suites**

```bash
cd libro_ml_dl
uv run --group validation ruff check scripts pruebas contenido_fuente
uv run --group validation ruff format --check scripts pruebas contenido_fuente
uv run --group validation --group notebooks python -m unittest discover \
  -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
cd ..
git diff --check
```

Expected: all checks pass.

- [ ] **Step 7: Commit notebook reproducibility**

```bash
git add verificar.sh libro_ml_dl/scripts/validar_notebooks.py \
  libro_ml_dl/pruebas/python/test_validar_notebooks.py
git commit -m "feat: validate source notebooks reproducibly"
```

---

### Task 5: Add a redacted local security gate

**Files:**
- Create: `verificar_seguridad.sh`
- Create: `libro_ml_dl/scripts/verificar_seguridad.py`
- Create: `libro_ml_dl/pruebas/python/test_verificar_seguridad.py`
- Modify: `libro_ml_dl/scripts/preparar_entorno.py`
- Modify: `libro_ml_dl/pruebas/python/test_preparar_entorno.py`

**Interfaces:**
- Consumes: `detect-secrets==1.5.0`, `pip-audit==2.10.1`, Git's tracked-file list, and `uv export`.
- Produces: `parse_secret_results(payload: dict[str, object]) -> list[SecretFinding]`, `find_personal_paths(repo_root: Path) -> list[Path]`, and `./verificar_seguridad.sh`, which never prints secret values.

- [ ] **Step 1: Write failing redaction and personal-path tests**

Create `libro_ml_dl/pruebas/python/test_verificar_seguridad.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.verificar_seguridad import (
    find_personal_paths,
    parse_secret_results,
    render_secret_findings,
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focal test and verify the security module is missing**

```bash
cd libro_ml_dl
uv run --group security --group validation python -m unittest \
  pruebas/python/test_verificar_seguridad.py -v
```

Expected: import error for `scripts.verificar_seguridad`.

- [ ] **Step 3: Implement redacted result parsing and path inspection**

Create `libro_ml_dl/scripts/verificar_seguridad.py` with these core interfaces:

```python
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BOOK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_ROOT.parent
EXCLUDED_FILES = (
    r"(^|/)(\.git|\.venv|\.ruff_cache|__pycache__|"
    r"assets/vendor/pyodide)/"
)
PERSONAL_USER = "rafa"
PERSONAL_PATH_MARKERS = (
    f"/Users/{PERSONAL_USER}/",
    f"/home/{PERSONAL_USER}/",
    f"C:\\Users\\{PERSONAL_USER}\\",
)


@dataclass(frozen=True, order=True)
class SecretFinding:
    path: str
    line_number: int
    detector_type: str


def parse_secret_results(payload: dict[str, Any]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path, entries in payload.get("results", {}).items():
        for entry in entries:
            findings.append(
                SecretFinding(
                    path=str(path),
                    line_number=int(entry["line_number"]),
                    detector_type=str(entry["type"]),
                )
            )
    return sorted(findings)


def render_secret_findings(findings: list[SecretFinding]) -> list[str]:
    return [
        f"{finding.path}:{finding.line_number} [{finding.detector_type}]"
        for finding in findings
    ]


def find_personal_paths(repo_root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or any(
            part in {".git", ".venv", ".ruff_cache", "__pycache__"}
            for part in path.parts
        ):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(marker in source for marker in PERSONAL_PATH_MARKERS):
            matches.append(path)
    return matches


def run_secret_scan(repo_root: Path) -> list[SecretFinding]:
    executable = shutil.which("detect-secrets")
    if executable is None:
        raise RuntimeError("detect-secrets no está instalado")
    completed = subprocess.run(
        [
            executable,
            "scan",
            "--no-verify",
            "--all-files",
            "--exclude-files",
            EXCLUDED_FILES,
            str(repo_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_secret_results(json.loads(completed.stdout))


def run_dependency_audit(book_root: Path) -> None:
    uv = shutil.which("uv")
    pip_audit = shutil.which("pip-audit")
    if uv is None or pip_audit is None:
        raise RuntimeError("uv y pip-audit deben estar instalados")
    with tempfile.NamedTemporaryFile(suffix=".txt") as requirements:
        subprocess.run(
            [
                uv,
                "export",
                "--frozen",
                "--group",
                "validation",
                "--group",
                "notebooks",
                "--group",
                "security",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
            ],
            cwd=book_root,
            check=True,
            stdout=requirements,
        )
        requirements.flush()
        subprocess.run(
            [
                pip_audit,
                "-r",
                requirements.name,
                "--progress-spinner",
                "off",
            ],
            check=True,
        )


def main() -> int:
    findings = run_secret_scan(REPO_ROOT)
    personal_paths = find_personal_paths(REPO_ROOT)
    if findings:
        for line in render_secret_findings(findings):
            print(f"POTENCIAL_SECRETO: {line}", file=sys.stderr)
    if personal_paths:
        for path in personal_paths:
            print(
                f"RUTA_PERSONAL: {path.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
    if findings or personal_paths:
        return 1
    run_dependency_audit(BOOK_ROOT)
    print("SEGURIDAD_PUBLICACION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Mark only the two verified checksums as non-secrets**

Add `# pragma: allowlist secret` to:

- the `CORE_SHA256` assignment in `scripts/preparar_entorno.py`;
- the literal SHA-256 assertion in
  `pruebas/python/test_preparar_entorno.py::test_sha256_file_uses_file_bytes`.

Do not add broad file exclusions or allowlist any credential-shaped value.

- [ ] **Step 5: Create the root security command**

Create executable `verificar_seguridad.sh`:

```sh
#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
book_root="$repo_root/libro_ml_dl"

cd "$book_root"
exec uv run --locked --group security python scripts/verificar_seguridad.py
```

Set the executable bit:

```bash
chmod +x verificar_seguridad.sh
```

- [ ] **Step 6: Run focal tests and the actual local security gate**

```bash
cd libro_ml_dl
uv run --group security --group validation python -m unittest \
  pruebas/python/test_verificar_seguridad.py -v
cd ..
./verificar_seguridad.sh
```

Expected: tests pass; `pip-audit` reports no known vulnerabilities; final line
is `SEGURIDAD_PUBLICACION_OK`; no candidate values are printed.

- [ ] **Step 7: Run complete unit and static checks**

```bash
cd libro_ml_dl
uv run --group validation --group notebooks --group security \
  python -m unittest discover -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
uv run --group validation ruff check scripts pruebas contenido_fuente
uv run --group validation ruff format --check scripts pruebas contenido_fuente
cd ..
python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
git diff --check
```

Expected: all checks pass.

- [ ] **Step 8: Commit the local security gate**

```bash
git add verificar_seguridad.sh libro_ml_dl/scripts/verificar_seguridad.py \
  libro_ml_dl/scripts/preparar_entorno.py libro_ml_dl/pruebas/python
git commit -m "feat: add redacted publication security gate"
```

---

### Task 6: Add licenses, provenance, reproducibility docs, and visual identity

**Files:**
- Create: `README.md`
- Create: `LICENSE-CODE`
- Create: `LICENSE-CONTENT`
- Create: `CITATION.cff`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `REPRODUCIBILITY.md`
- Create: `material_fuente/README.md`
- Create: `assets/branding/easy-machine-learning-banner.png`
- Create: `pruebas_publicacion/test_documentacion.py`
- Modify: `libro_ml_dl/README.md`

**Interfaces:**
- Consumes: root commands from Tasks 3 and 5, approved dual licensing, notebook hashes from Task 1, and the approved “From pixels to intelligence” direction.
- Produces: a reader-facing repository contract, verifiable licenses/provenance, and one project-owned PNG banner referenced by the root README.

- [ ] **Step 1: Write failing documentation and banner tests**

Create `pruebas_publicacion/test_documentacion.py`:

```python
from __future__ import annotations

import struct
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_required_publication_documents_exist(self) -> None:
        for relative_path in (
            "README.md",
            "LICENSE-CODE",
            "LICENSE-CONTENT",
            "CITATION.cff",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "REPRODUCIBILITY.md",
            "material_fuente/README.md",
        ):
            self.assertTrue((REPO_ROOT / relative_path).is_file(), relative_path)

    def test_readme_documents_clone_install_launch_and_verify(self) -> None:
        source = REPO_ROOT.joinpath("README.md").read_text(encoding="utf-8")
        for command in (
            "gh repo clone rafaamarin/easy-machine-learning",
            "./instalar.sh",
            "./lanzar.sh",
            "./verificar.sh",
            "./verificar_seguridad.sh",
        ):
            self.assertIn(command, source)
        self.assertIn("assets/branding/easy-machine-learning-banner.png", source)

    def test_banner_is_a_large_landscape_png(self) -> None:
        path = REPO_ROOT / "assets/branding/easy-machine-learning-banner.png"
        data = path.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertGreaterEqual(width, 1200)
        self.assertGreaterEqual(height, 600)
        self.assertGreater(width / height, 1.5)

    def test_licenses_cover_code_and_content(self) -> None:
        code_license = REPO_ROOT.joinpath("LICENSE-CODE").read_text(
            encoding="utf-8"
        )
        content_license = REPO_ROOT.joinpath("LICENSE-CONTENT").read_text(
            encoding="utf-8"
        )
        self.assertIn("MIT License", code_license)
        self.assertIn("Creative Commons Attribution 4.0", content_license)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify publication documents are absent**

```bash
python3 -m unittest pruebas_publicacion/test_documentacion.py -v
```

Expected: failures for missing documents and banner.

- [ ] **Step 3: Create the dual licenses and citation metadata**

Create `LICENSE-CODE` with the complete standard MIT License text, copyright
`2026 Rafael Marín`.

Create `LICENSE-CONTENT` with this header followed by the verbatim CC BY 4.0
legal code from `https://creativecommons.org/licenses/by/4.0/legalcode.txt`:

```text
Easy Machine Learning educational text, notebooks, and visual assets are
licensed under the Creative Commons Attribution 4.0 International license.

SPDX-License-Identifier: CC-BY-4.0
Official license: https://creativecommons.org/licenses/by/4.0/
```

Create `CITATION.cff`:

```yaml
cff-version: 1.2.0
message: "Si utilizas este recurso, cita Easy Machine Learning."
title: "Easy Machine Learning"
type: software
authors:
  - family-names: "Marín"
    given-names: "Rafael"
repository-code: "https://github.com/rafaamarin/easy-machine-learning"
version: "0.1.0"
date-released: "2026-08-23"
license: "MIT AND CC-BY-4.0"
```

- [ ] **Step 4: Document provenance and reproducibility**

Create `material_fuente/README.md` with a table containing each exact filename,
its approved SHA-256, its original vault path, and its contribution to module
01. State that redistribution permission was confirmed by the repository owner
on 2026-08-23 and that the notebooks are preserved byte for byte under CC BY
4.0.

Create `REPRODUCIBILITY.md` with these exact sections and commands:

````markdown
# Reproducibilidad

## Sistemas soportados

- macOS arm64/x86_64.
- Linux arm64/x86_64.
- Windows mediante WSL 2.
- Python 3.11 o posterior.

## Desde un clon vacío

```bash
gh repo clone rafaamarin/easy-machine-learning
cd easy-machine-learning
./instalar.sh
./verificar.sh
./lanzar.sh
```

## Instalación no interactiva para CI

```bash
./instalar.sh --yes
```

## Modo web ligero

```bash
cd libro_ml_dl
python3 -m http.server 8000 --bind 127.0.0.1
```

## Qué no modifica la instalación

No instala kernels globales, no escribe fuera del repositorio salvo caches de
`uv`, no cambia los notebooks fuente y no expone servicios fuera de loopback.
````

Add troubleshooting for missing `uv`, occupied ports, absent Pyodide, WSL
browser opening, and Jupyter fallback, using the exact error text emitted by the
scripts.

- [ ] **Step 5: Create the contributor and security contracts**

Create `CONTRIBUTING.md` with this contributor flow:

```bash
./instalar.sh --yes
./verificar.sh
./verificar_seguridad.sh
git diff --check
```

Require snake_case Python, focused tests, source-notebook preservation, no
generated Pyodide binaries, and no claims that roadmap modules are complete.

Create `SECURITY.md` stating:

- supported version: `0.1.x`;
- never open a public issue containing a credential;
- use GitHub private vulnerability reporting when enabled;
- otherwise contact the repository owner through the private repository;
- revoke and rotate any exposed credential before remediation;
- `./verificar_seguridad.sh` is the local security command.

- [ ] **Step 6: Generate and inspect the project banner**

The executing controller must read and use the `imagegen` skill. Generate one
project-bound raster asset with the built-in image generation tool using this
prompt:

```text
Use case: scientific-educational
Asset type: panoramic GitHub README banner
Primary request: visualize the journey from pixels to machine intelligence
Scene/backdrop: dark technical blueprint field with subtle grid and depth
Subject: left-to-right transition from a pixel image grid, through tensors and
neural-network connections, into clean transformer attention blocks
Style/medium: premium editorial scientific illustration, precise and modern
Composition/framing: wide landscape, balanced visual flow, safe margins, strong
center line, readable when scaled down
Lighting/mood: luminous but restrained, engineering-focused, optimistic
Color palette: deep navy, electric blue, cyan, with one restrained warm accent
Text: none
Constraints: no logos, no people, no branded symbols, no equations presented as
facts, no watermark, no text, no fake UI
Avoid: corporate stock-art style, visual clutter, neon overload, illegible labels
```

Inspect the generated image, select only a clean text-free result, copy it to
`assets/branding/easy-machine-learning-banner.png`, and confirm the test's PNG,
minimum-size, and aspect-ratio requirements. Record the final prompt and built-in
tool mode in the task report.

- [ ] **Step 7: Build the root README and align the book README**

Create `README.md` with this section order:

1. banner image with alt text “De píxeles a tensores, redes y atención”;
2. `# Easy Machine Learning`;
3. one-sentence Spanish value proposition;
4. honest “Disponible ahora” list: platform, module 00, module 01, five editable
   labs, two figures, local Pyodide, optional JupyterLab;
5. “Descargar” with authenticated `gh repo clone`, authenticated `git clone`, and
   GitHub Download ZIP instructions;
6. “Instalar y ejecutar” with `./instalar.sh` and `./lanzar.sh`;
7. “Reproducir y verificar” with both verification commands;
8. repository structure;
9. notebook provenance link;
10. roadmap that labels TensorFlow, PyTorch, vision, transformers, engineering,
    and projects as planned rather than available;
11. dual-license and citation summary;
12. supported-platform limitations.

Use these badge targets after the repository URL is known:

```markdown
[![Validación](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/validar.yml/badge.svg)](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/validar.yml)
[![Seguridad](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/seguridad.yml/badge.svg)](https://github.com/rafaamarin/easy-machine-learning/actions/workflows/seguridad.yml)
```

Update `libro_ml_dl/README.md` so setup commands point to the root wrappers and
remove course-specific `unir-tf` instructions.

- [ ] **Step 8: Run documentation, provenance, and full unit tests**

```bash
python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
cd libro_ml_dl
uv run --group validation --group notebooks --group security \
  python -m unittest discover -s pruebas/python -p 'test_*.py' -v
node --test pruebas/js/*.test.mjs
uv run --group validation ruff check scripts pruebas contenido_fuente
uv run --group validation ruff format --check scripts pruebas contenido_fuente
cd ..
./verificar_seguridad.sh
git diff --check
```

Expected: all checks pass and `SEGURIDAD_PUBLICACION_OK` is printed.

- [ ] **Step 9: Commit documentation and branding**

```bash
git add README.md LICENSE-CODE LICENSE-CONTENT CITATION.cff CONTRIBUTING.md \
  SECURITY.md REPRODUCIBILITY.md material_fuente/README.md \
  assets/branding/easy-machine-learning-banner.png pruebas_publicacion \
  libro_ml_dl/README.md
git commit -m "docs: add reproducibility licenses and visual identity"
```

---

### Task 7: Add pinned CI and dependency update automation

**Files:**
- Create: .github/workflows/validar.yml
- Create: .github/workflows/seguridad.yml
- Create: .github/dependabot.yml
- Create: pruebas_publicacion/test_ci_config.py

**Interfaces:**
- Consumes: the root functional and security commands.
- Produces: a fast Ubuntu/macOS matrix, a full clean-install Ubuntu gate, a
  separate security workflow, and weekly dependency update proposals.

- [ ] **Step 1: Write failing CI-policy tests**

Create pruebas_publicacion/test_ci_config.py:

~~~python
from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = (
    "3d3c42e5aac5ba805825da76"  # pragma: allowlist secret
    "410c181273ba90b1"  # pragma: allowlist secret
)
SETUP_UV_SHA = (
    "c771a70e6277c0a99b617c7a"  # pragma: allowlist secret
    "806ffedaca235ff9"  # pragma: allowlist secret
)
SETUP_NODE_SHA = (
    "820762786026740c76f36085"  # pragma: allowlist secret
    "b0efc47a31fe5020"  # pragma: allowlist secret
)


class ContinuousIntegrationTests(unittest.TestCase):
    def test_required_automation_files_exist(self) -> None:
        for relative_path in (
            ".github/workflows/validar.yml",
            ".github/workflows/seguridad.yml",
            ".github/dependabot.yml",
        ):
            self.assertTrue((REPO_ROOT / relative_path).is_file(), relative_path)

    def test_workflows_pin_actions_and_use_read_only_permissions(self) -> None:
        for name in ("validar.yml", "seguridad.yml"):
            source = REPO_ROOT.joinpath(
                ".github", "workflows", name
            ).read_text(encoding="utf-8")
            self.assertIn(f"actions/checkout@{CHECKOUT_SHA}", source)
            self.assertIn(f"astral-sh/setup-uv@{SETUP_UV_SHA}", source)
            self.assertIn("permissions:\n  contents: read", source)
            self.assertNotIn("pull_request_target", source)
            self.assertIsNone(
                re.search(r"uses:\s+\S+@(main|master|v\d+)\s*$", source, re.M)
            )

    def test_validation_workflow_pins_node_and_covers_platforms(self) -> None:
        source = REPO_ROOT.joinpath(
            ".github", "workflows", "validar.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(f"actions/setup-node@{SETUP_NODE_SHA}", source)
        self.assertIn("ubuntu-latest", source)
        self.assertIn("macos-latest", source)
        self.assertIn("./instalar.sh --yes", source)
        self.assertIn("./verificar.sh", source)

    def test_dependabot_covers_uv_and_github_actions(self) -> None:
        source = REPO_ROOT.joinpath(
            ".github", "dependabot.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('package-ecosystem: "uv"', source)
        self.assertIn('directory: "/libro_ml_dl"', source)
        self.assertIn('package-ecosystem: "github-actions"', source)
        self.assertIn('directory: "/"', source)


if __name__ == "__main__":
    unittest.main()
~~~

- [ ] **Step 2: Run the focal test and confirm automation is absent**

~~~bash
python3 -m unittest pruebas_publicacion/test_ci_config.py -v
~~~

Expected: failures for the three missing files.

- [ ] **Step 3: Create the pinned validation workflow**

Create .github/workflows/validar.yml:

~~~yaml
name: Validación

on:
  push:
    branches: ["main"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: validacion-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  comprobaciones-rapidas:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: ubuntu-latest
            python: "3.11"
          - os: macos-latest
            python: "3.13"
    runs-on: ${{ matrix.os }}
    steps:
      - name: Descargar código
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Preparar Python y uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
        with:
          version: "0.12.5"
          python-version: ${{ matrix.python }}
          enable-cache: true
      - name: Preparar Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: "22"
      - name: Sincronizar sin descargar Pyodide
        working-directory: libro_ml_dl
        run: uv sync --locked --group validation --group notebooks --group security
      - name: Verificar publicación
        run: python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
      - name: Verificar Python
        working-directory: libro_ml_dl
        run: |
          uv run --locked --group validation --group notebooks --group security \
            python -m unittest discover -s pruebas/python -p 'test_*.py' -v
          uv run --locked --group validation ruff check scripts pruebas contenido_fuente
          uv run --locked --group validation ruff format --check \
            scripts pruebas contenido_fuente
      - name: Verificar JavaScript
        working-directory: libro_ml_dl
        run: node --test pruebas/js/*.test.mjs

  instalacion-limpia:
    needs: comprobaciones-rapidas
    runs-on: ubuntu-latest
    steps:
      - name: Descargar código
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Preparar Python y uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
        with:
          version: "0.12.5"
          python-version: "3.11"
          enable-cache: true
      - name: Preparar Node
        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: "22"
      - name: Instalar desde cero
        run: ./instalar.sh --yes
      - name: Ejecutar gate funcional completo
        run: ./verificar.sh
~~~

- [ ] **Step 4: Create the isolated security workflow**

Create .github/workflows/seguridad.yml:

~~~yaml
name: Seguridad

on:
  push:
    branches: ["main"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: seguridad-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  auditoria:
    runs-on: ubuntu-latest
    steps:
      - name: Descargar código e historial
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
      - name: Preparar Python y uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
        with:
          version: "0.12.5"
          python-version: "3.11"
          enable-cache: true
      - name: Instalar herramientas fijadas
        working-directory: libro_ml_dl
        run: uv sync --locked --group validation --group notebooks --group security
      - name: Escanear secretos, rutas y dependencias
        run: ./verificar_seguridad.sh
~~~

Keep fetch-depth at zero: the publication audit must inspect every local commit,
not only the tip. Reports may contain commit, path, line, and detector, but
never the candidate value.

- [ ] **Step 5: Configure weekly dependency proposals**

Create .github/dependabot.yml:

~~~yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/libro_ml_dl"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels: ["dependencies", "python"]
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels: ["dependencies", "github-actions"]
~~~

- [ ] **Step 6: Run automation policy and local gates**

~~~bash
python3 -m unittest pruebas_publicacion/test_ci_config.py -v
./verificar.sh
./verificar_seguridad.sh
git diff --check
~~~

Expected: tests and both gates pass. No workflow uses a mutable action tag.

- [ ] **Step 7: Commit automation**

~~~bash
git add .github pruebas_publicacion/test_ci_config.py
git commit -m "ci: validate reproducibility and security"
~~~

---

### Task 8: Complete independent review, clean-clone rehearsal, and audit

**Files:**
- Create: docs/security-audit.md
- Create: pruebas_publicacion/test_publication_hygiene.py
- Modify as required: only files implicated by verified review findings

**Interfaces:**
- Consumes: full local history, all gates, the browser-facing book, and an
  independent code review.
- Produces: zero Critical/Important findings, a clean-clone proof, and a
  redacted audit tied to the release commit.
- Adds: `scan_git_history(repo_root: Path) -> list[HistoricalFinding]`, where
  `HistoricalFinding` contains only commit, path, line, and detector metadata.

- [ ] **Step 1: Write failing repository-hygiene tests**

Create pruebas_publicacion/test_publication_hygiene.py:

~~~python
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

    def test_local_environments_and_runtime_downloads_are_not_tracked(self) -> None:
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
~~~

- [ ] **Step 2: Run the hygiene test and confirm the audit is absent**

~~~bash
python3 -m unittest pruebas_publicacion/test_publication_hygiene.py -v
~~~

Expected: only the audit-document test fails.

- [ ] **Step 3: Implement and run complete Git-history scanning**

Modify `libro_ml_dl/scripts/verificar_seguridad.py` and its focal test to:

1. enumerate commits with git rev-list --all;
2. export each tree with git archive into a TemporaryDirectory;
3. call the same redacted detect-secrets parser on each tree;
4. classify only the two already verified checksum findings from the initial
   import by repository-relative file and line;
5. fail for every other finding and report only commit, path, line, and detector;
6. scan the same snapshots for personal absolute paths;
7. clean temporary directories through their context managers.

Add focused tests with a temporary Git repository containing one benign commit
and one credential-shaped fixture. Assert that the failing report omits the
fixture value. Run:

~~~bash
cd libro_ml_dl
uv run --group security --group validation python -m unittest \
  pruebas/python/test_verificar_seguridad.py -v
cd ..
./verificar_seguridad.sh
~~~

Expected: the current tree and every historical tree pass. The output names the
two adjudicated checksum locations, never their values.

- [ ] **Step 4: Run browser acceptance against the real launcher**

Start ./lanzar.sh --sin-jupyter --sin-navegador in a managed terminal session.
Load and use the browser:control-in-app-browser skill, then verify:

1. the home page loads from loopback;
2. the complete interactive index is reachable;
3. one Pyodide exercise executes and shows a result;
4. a hyperparameter control changes the displayed output;
5. a collapsed solution opens and closes;
6. there are no blocking console or network errors.

Capture one screenshot for review but do not add it unless it improves the
reader-facing README. Stop the launcher cleanly with SIGINT. If browser control
is unavailable, use curl --fail for HTTP readiness and record the missing
interactive acceptance under audit limitations; never claim it ran.

- [ ] **Step 5: Request and resolve independent code review**

Load and use superpowers:requesting-code-review. Give the reviewer the design
spec, this plan, the complete diff from the initial design commit, and the
functional/security outputs. Require severity labels and explicit checks for:

- source fidelity and licensing;
- path traversal and worker lifecycle fixes;
- shell portability and loopback binding;
- notebook byte preservation and isolated execution;
- scan redaction and history coverage;
- pinned CI permissions;
- truthful README capability claims.

Use superpowers:receiving-code-review for findings. Verify each finding before
changing code. Repeat review until there are zero Critical or Important
findings, then rerun both full gates.

- [ ] **Step 6: Rehearse from a genuinely clean local clone**

Run from the repository root:

~~~bash
rehearsal_root=$(mktemp -d)
rehearsal_clone="$rehearsal_root/easy-machine-learning"
git clone --local . "$rehearsal_clone"
cd "$rehearsal_clone"
./instalar.sh --yes
./verificar.sh
./verificar_seguridad.sh
cd ..
/usr/bin/trash "$rehearsal_root"
~~~

Expected: installation starts with no .venv or Pyodide runtime, all three
commands pass, and the disposable clone is moved to Trash after evidence is
captured.

- [ ] **Step 7: Write the redacted security audit from live outputs**

Create docs/security-audit.md in Spanish. Record:

- audit date and exact candidate release commit;
- tracked file count, total tracked bytes, and absence of symlinks;
- source book commit/tree and three approved notebook hashes;
- notebook execution summaries and unchanged source hashes;
- detect-secrets 1.5.0 result for current tree and every Git commit;
- the two checksum false-positive locations, without values;
- pip-audit 2.10.1 dependency count and vulnerability result;
- personal-path, ignored-artifact, and oversized-file results;
- clean-clone commands and outcome;
- browser acceptance outcome;
- independent reviewer identifier, reviewed range, and zero
  Critical/Important result;
- limitations, including GitHub account-plan features not yet verifiable.

Do not copy terminal output that could contain tokens or machine-local paths.

- [ ] **Step 8: Run the final local release gate and commit the audit**

~~~bash
python3 -m unittest discover -s pruebas_publicacion -p 'test_*.py' -v
./verificar.sh
./verificar_seguridad.sh
git diff --check
git status --short
git add docs/security-audit.md pruebas_publicacion/test_publication_hygiene.py \
  libro_ml_dl/scripts/verificar_seguridad.py \
  libro_ml_dl/pruebas/python/test_verificar_seguridad.py
git commit -m "docs: record pre-publication security audit"
./verificar.sh
./verificar_seguridad.sh
git status --short
~~~

Expected: both post-commit gates pass and the worktree is empty.

---

### Task 9: Create and verify the private GitHub repository

**Files:**
- No planned repository file changes unless a real GitHub Actions failure
  requires a narrowly scoped fix.

**Interfaces:**
- Consumes: a clean, reviewed, security-approved local main.
- Produces: private rafaamarin/easy-machine-learning, matching local/remote
  heads, metadata, supported security settings, and green remote workflows.

- [ ] **Step 1: Recheck account, name, branch, and local release state**

~~~bash
gh auth status
git branch --show-current
git status --short
./verificar.sh
./verificar_seguridad.sh
if gh repo view rafaamarin/easy-machine-learning >/dev/null 2>&1; then
  echo "ERROR: el repositorio remoto ya existe; no se sobrescribe." >&2
  exit 1
fi
~~~

Expected: authenticated as rafaamarin, branch main, empty worktree, both gates
green, and the remote name available. Never print the auth token.

- [ ] **Step 2: Create and push the private repository**

This controller-only external side effect is already authorized by the user:

~~~bash
gh repo create rafaamarin/easy-machine-learning \
  --private \
  --source=. \
  --remote=origin \
  --push \
  --description "Libro interactivo y práctico de Machine Learning en español, ejecutable localmente con Pyodide y JupyterLab" \
  --disable-wiki
~~~

Do not change visibility. If creation fails, inspect the error without retrying
against another owner or name.

- [ ] **Step 3: Apply topics and supported security settings**

~~~bash
gh api --method PUT repos/rafaamarin/easy-machine-learning/topics \
  --input - <<'JSON'
{"names":["machine-learning","python","jupyter","pyodide","education","spanish","local-first"]}
JSON

gh api --method PUT \
  repos/rafaamarin/easy-machine-learning/vulnerability-alerts
~~~

Attempt secret scanning and push protection through the official repository
security API. Treat HTTP 403/422 as an account-plan limitation: leave the
repository private, preserve the successful push, and record the unsupported
feature. Do not weaken visibility or expose code to obtain it.

- [ ] **Step 4: Prove remote identity, privacy, and commit equality**

~~~bash
local_head=$(git rev-parse HEAD)
remote_head=$(git ls-remote origin refs/heads/main | cut -f1)
test "$local_head" = "$remote_head"
git remote get-url origin
gh repo view rafaamarin/easy-machine-learning \
  --json nameWithOwner,url,visibility,defaultBranchRef
~~~

Expected: visibility is PRIVATE, default branch is main, and both hashes are
identical.

- [ ] **Step 5: Watch both remote workflows to completion**

For each of validar.yml and seguridad.yml, locate the run for $local_head:

~~~bash
gh run list --commit "$local_head" --limit 10 \
  --json databaseId,name,status,conclusion,url
gh run watch RUN_ID --exit-status
~~~

Replace RUN_ID with the returned numeric identifier during execution. If a
workflow fails, keep the repository private, load
superpowers:systematic-debugging, inspect only redacted logs, implement the
smallest verified fix, rerun local gates and review, commit, push, and watch the
replacement run. Do not finish while either workflow is red.

- [ ] **Step 6: Deliver the private repository**

Report:

- private URL and exact remote commit;
- authenticated clone and Download ZIP instructions;
- ./instalar.sh, ./lanzar.sh, ./verificar.sh, and
  ./verificar_seguridad.sh;
- supported platforms and WSL limitation;
- included book/notebook scope and roadmap boundaries;
- security scan, dependency audit, clean-clone, browser, and CI results;
- any GitHub security feature blocked by the account plan;
- reminder that making the repository public requires a separate instruction.

Do not claim success until the private remote, commit equality, and both
workflow conclusions have been verified.
