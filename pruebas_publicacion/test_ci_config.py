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

    def test_validation_matrix_selects_uv_python_explicitly(self) -> None:
        source = REPO_ROOT.joinpath(
            ".github", "workflows", "validar.yml"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            source,
            r"comprobaciones-rapidas:\n(?:.*\n)*?    env:\n"
            r"      UV_PYTHON: \$\{\{ matrix\.python \}\}",
        )

    def test_security_matrix_binds_each_os_to_its_python(self) -> None:
        source = REPO_ROOT.joinpath(
            ".github", "workflows", "seguridad.yml"
        ).read_text(encoding="utf-8")
        for entry in (
            '- os: ubuntu-latest\n            python: "3.11"',
            '- os: macos-latest\n            python: "3.13"',
        ):
            self.assertIn(entry, source)
        self.assertIn("runs-on: ${{ matrix.os }}", source)
        self.assertIn("UV_PYTHON: ${{ matrix.python }}", source)
        self.assertIn("python-version: ${{ matrix.python }}", source)
        self.assertIn(
            "uv sync --locked --group validation --group notebooks --group security",
            source,
        )
        self.assertIn("./verificar_seguridad.sh", source)

    def test_validation_publication_tests_use_project_uv_python(self) -> None:
        source = REPO_ROOT.joinpath(
            ".github", "workflows", "validar.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "uv run --project libro_ml_dl --locked --group validation",
            source,
        )
        self.assertNotIn(
            "run: python3 -m unittest discover -s pruebas_publicacion",
            source,
        )

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
