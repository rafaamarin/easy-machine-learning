from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

BOOK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BOOK_ROOT.parent
EXCLUDED_DIRECTORIES = {
    ".git",
    ".superpowers",
    ".venv",
    ".ruff_cache",
    "__pycache__",
}
PERSONAL_USER = "rafa"
PERSONAL_PATH_MARKERS = (
    f"/Users/{PERSONAL_USER}/",
    f"/home/{PERSONAL_USER}/",
    f"C:\\Users\\{PERSONAL_USER}\\",
)
PERSONAL_PATH_MARKER_BYTES = tuple(
    marker.encode("ascii") for marker in PERSONAL_PATH_MARKERS
)
SECRET_SCAN_CHUNK_SIZE = 200
APPROVED_CORE_SHA256 = "".join(
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
APPROVED_ABC_SHA256 = hashlib.sha256(b"abc").hexdigest()


@dataclass(frozen=True, order=True)
class SecretFinding:
    path: str
    line_number: int
    detector_type: str


@dataclass(frozen=True, order=True)
class SecretApproval:
    path: str
    line_number: int
    detector_type: str
    approved_value: str
    exact_syntax: str


@dataclass(frozen=True)
class SecretScanResult:
    rejected: tuple[SecretFinding, ...]
    adjudicated: tuple[SecretFinding, ...]
    personal_findings: tuple[SecretFinding, ...]


@dataclass(frozen=True, order=True)
class HistoricalFinding:
    commit: str
    path: str
    line_number: int
    detector_type: str


@dataclass(frozen=True, order=True)
class GitTreeEntry:
    path: str
    object_id: str
    mode: str


class HistoricalScanError(RuntimeError):
    def __init__(self, findings: list[HistoricalFinding]) -> None:
        self.findings = sorted(findings)
        super().__init__("hallazgos históricos no adjudicados")


def _joined(*chunks: str) -> str:
    return "".join(chunks)


APPROVED_NOTEBOOK_PARTS = (
    _joined("15f0a0f4", "137ba811", "17f8bacf", "90dbd341"),
    _joined("82833596", "3191b2fd", "c3a21365", "0df510ea"),
    _joined("f4352008", "a8f973f4", "96dba58c", "08740b25"),
    _joined("0daac81b", "20b94ba3", "b1eac86b", "2221e30a"),
    _joined("894a588d", "2eb24d02", "d032ac61", "a2f2961e"),
    _joined("ef1920a9", "c6cfdb17", "e50948d0", "612dbeaf"),
)
APPROVED_ACTION_PARTS = (
    _joined("3d3c42e5", "aac5ba80", "5825da76"),
    _joined("410c1812", "73ba90b1"),
    _joined("c771a70e", "6277c0a9", "9b617c7a"),
    _joined("806ffeda", "ca235ff9"),
    _joined("82076278", "6026740c", "76f36085"),
    _joined("b0efc47a", "31fe5020"),
)


def _approval(
    path: str,
    line_number: int,
    value: str,
    exact_syntax: str,
) -> SecretApproval:
    return SecretApproval(
        path=path,
        line_number=line_number,
        detector_type="Hex High Entropy String",
        approved_value=value,
        exact_syntax=exact_syntax,
    )


def _approved_secret_registry() -> tuple[SecretApproval, ...]:
    records = [
        _approval(
            "libro_ml_dl/scripts/preparar_entorno.py",
            17,
            APPROVED_CORE_SHA256,
            f'CORE_SHA256 = "{APPROVED_CORE_SHA256}"',
        ),
        _approval(
            "libro_ml_dl/scripts/preparar_entorno.py",
            17,
            APPROVED_CORE_SHA256,
            f'CORE_SHA256 = "{APPROVED_CORE_SHA256}"  '
            "# pragma: allowlist secret  # noqa: E501",
        ),
        _approval(
            "libro_ml_dl/pruebas/python/test_preparar_entorno.py",
            81,
            APPROVED_ABC_SHA256,
            f'                "{APPROVED_ABC_SHA256}",',
        ),
        _approval(
            "libro_ml_dl/pruebas/python/test_preparar_entorno.py",
            81,
            APPROVED_ABC_SHA256,
            f'                "{APPROVED_ABC_SHA256}",  '
            "# pragma: allowlist secret  # noqa: E501",
        ),
    ]
    for notebook_lines in (
        (12, 13, 16, 17, 20, 21),
        (13, 14, 17, 18, 21, 22),
    ):
        for line_number, value in zip(
            notebook_lines,
            APPROVED_NOTEBOOK_PARTS,
            strict=True,
        ):
            syntax = f'        "{value}"  # pragma: allowlist secret'
            records.append(
                _approval(
                    "pruebas_publicacion/test_material_fuente.py",
                    line_number,
                    value,
                    syntax,
                )
            )
    for line_number, value in zip(
        (71, 72, 75, 76, 79, 80),
        APPROVED_NOTEBOOK_PARTS,
        strict=True,
    ):
        syntax = f'        "{value}"  # pragma: allowlist secret'
        records.append(
            _approval(
                "docs/superpowers/plans/"
                "2026-08-23-easy-machine-learning-publication.md",
                line_number,
                value,
                syntax,
            )
        )
    for line_number, value in zip(
        (10, 11, 14, 15, 18, 19),
        APPROVED_ACTION_PARTS,
        strict=True,
    ):
        syntax = f'    "{value}"  # pragma: allowlist secret'
        records.append(
            _approval(
                "pruebas_publicacion/test_ci_config.py",
                line_number,
                value,
                syntax,
            )
        )
    for line_number, value in zip(
        (1639, 1640, 1643, 1644, 1647, 1648),
        APPROVED_ACTION_PARTS,
        strict=True,
    ):
        syntax = f'    "{value}"  # pragma: allowlist secret'
        records.append(
            _approval(
                "docs/superpowers/plans/"
                "2026-08-23-easy-machine-learning-publication.md",
                line_number,
                value,
                syntax,
            )
        )
    return tuple(records)


APPROVED_SECRET_REGISTRY = _approved_secret_registry()


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
        f"{_escape_metadata(finding.path)}:{finding.line_number} "
        f"[{_escape_metadata(finding.detector_type)}]"
        for finding in findings
    ]


def render_historical_findings(
    findings: list[HistoricalFinding],
) -> list[str]:
    return [
        f"{_escape_metadata(finding.commit)} "
        f"{_escape_metadata(finding.path)}:{finding.line_number} "
        f"[{_escape_metadata(finding.detector_type)}]"
        for finding in findings
    ]


def _escape_metadata(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)[1:-1]


def _normalize_secret_paths(
    findings: list[SecretFinding],
    repo_root: Path,
) -> list[SecretFinding]:
    normalized: list[SecretFinding] = []
    resolved_root = repo_root.resolve()
    for finding in findings:
        path = Path(finding.path)
        try:
            relative_path = (
                path.resolve().relative_to(resolved_root)
                if path.is_absolute()
                else path
            )
        except ValueError as error:
            raise RuntimeError(
                "detect-secrets devolvió una ruta fuera del repositorio"
            ) from error
        if ".." in relative_path.parts:
            raise RuntimeError("detect-secrets devolvió una ruta fuera del repositorio")
        normalized.append(
            SecretFinding(
                path=relative_path.as_posix(),
                line_number=finding.line_number,
                detector_type=finding.detector_type,
            )
        )
    return sorted(normalized)


def _is_excluded_candidate(path: Path, repo_root: Path) -> bool:
    relative_path = path.relative_to(repo_root)
    if path.is_symlink():
        raise RuntimeError("el inventario contiene un enlace simbólico")
    return (
        not path.is_file()
        or any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts)
        or relative_path.parts[:4] == ("libro_ml_dl", "assets", "vendor", "pyodide")
    )


def _candidate_files(repo_root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
    except OSError:
        completed = None
    if completed is not None and completed.returncode == 0:
        try:
            relative_paths = [
                relative_path.decode("utf-8")
                for relative_path in completed.stdout.split(b"\0")
                if relative_path
            ]
        except UnicodeDecodeError as error:
            raise RuntimeError(
                "el inventario contiene un nombre que no es UTF-8"
            ) from error
        paths = sorted(repo_root / path for path in relative_paths)
        for path in paths:
            if path.is_symlink():
                raise RuntimeError("el inventario contiene un enlace simbólico")
            if not path.is_file():
                raise RuntimeError("el inventario contiene un archivo no disponible")
        return paths
    else:
        if repo_root.joinpath(".git").exists():
            raise RuntimeError("no se pudo obtener el inventario de Git")
        paths = sorted(repo_root.rglob("*"))
    return [path for path in paths if not _is_excluded_candidate(path, repo_root)]


def _find_personal_path_findings(
    repo_root: Path,
    candidates: list[Path] | None = None,
) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    candidate_files = _candidate_files(repo_root) if candidates is None else candidates
    for path in candidate_files:
        try:
            source = path.read_bytes()
        except OSError as error:
            raise RuntimeError("no se pudo inspeccionar una ruta personal") from error
        relative_path = path.relative_to(repo_root).as_posix()
        for line_number, line in enumerate(source.splitlines(), start=1):
            if any(marker in line for marker in PERSONAL_PATH_MARKER_BYTES):
                findings.append(
                    SecretFinding(relative_path, line_number, "Ruta personal")
                )
    return sorted(findings)


def find_personal_paths(repo_root: Path) -> list[Path]:
    return sorted(
        {
            repo_root / finding.path
            for finding in _find_personal_path_findings(repo_root)
        }
    )


def run_secret_scan(
    repo_root: Path,
    candidates: list[Path] | None = None,
    *,
    only_allowlisted: bool = False,
) -> list[SecretFinding]:
    executable = shutil.which("detect-secrets")
    if executable is None:
        raise RuntimeError("detect-secrets no está instalado")
    candidate_files = _candidate_files(repo_root) if candidates is None else candidates
    findings: list[SecretFinding] = []
    for start in range(0, len(candidate_files), SECRET_SCAN_CHUNK_SIZE):
        chunk = candidate_files[start : start + SECRET_SCAN_CHUNK_SIZE]
        relative_paths = [path.relative_to(repo_root).as_posix() for path in chunk]
        command = [executable, "scan", "--no-verify"]
        if only_allowlisted:
            command.append("--only-allowlisted")
        completed = subprocess.run(
            [*command, "--", *relative_paths],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError("detect-secrets no pudo escanear el inventario")
        findings.extend(parse_secret_results(json.loads(completed.stdout)))
    return _normalize_secret_paths(findings, repo_root)


def _materialize_allowlist_scan_view(
    repo_root: Path,
    candidates: list[Path],
    snapshot_root: Path,
) -> list[Path]:
    scan_candidates: list[Path] = []
    for path in candidates:
        try:
            source = path.read_bytes()
            relative_path = path.relative_to(repo_root)
            destination = snapshot_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            scan_source = source.decode("utf-8", errors="replace").encode("utf-8")
            destination.write_bytes(scan_source or b"\n")
        except OSError as error:
            raise RuntimeError("no se pudo preparar el pase de supresiones") from error
        scan_candidates.append(destination)
    return scan_candidates


def _is_approved_secret(
    snapshot_root: Path,
    finding: SecretFinding,
) -> bool:
    matching_records = [
        record
        for record in APPROVED_SECRET_REGISTRY
        if (
            record.path == finding.path
            and record.line_number == finding.line_number
            and record.detector_type == finding.detector_type
        )
    ]
    if not matching_records:
        return False
    try:
        source_line = (
            snapshot_root.joinpath(finding.path)
            .read_text(encoding="utf-8")
            .splitlines()[finding.line_number - 1]
        )
    except (IndexError, OSError, UnicodeDecodeError):
        return False
    return any(
        source_line == record.exact_syntax
        and source_line.count(record.approved_value) == 1
        for record in matching_records
    )


def scan_security_snapshot(
    repo_root: Path,
    candidates: list[Path] | None = None,
) -> SecretScanResult:
    candidate_files = _candidate_files(repo_root) if candidates is None else candidates
    normal_findings = run_secret_scan(repo_root, candidate_files)
    with tempfile.TemporaryDirectory(prefix="easy_ml_allowlist_") as directory:
        allowlist_root = Path(directory) / "snapshot"
        allowlist_root.mkdir()
        allowlist_candidates = _materialize_allowlist_scan_view(
            repo_root,
            candidate_files,
            allowlist_root,
        )
        allowlisted_findings = run_secret_scan(
            allowlist_root,
            allowlist_candidates,
            only_allowlisted=True,
        )
    combined = [*normal_findings, *allowlisted_findings]
    location_counts = Counter(
        (finding.path, finding.line_number) for finding in combined
    )
    rejected: list[SecretFinding] = []
    adjudicated: list[SecretFinding] = []
    for finding in combined:
        location = (finding.path, finding.line_number)
        if location_counts[location] == 1 and _is_approved_secret(
            repo_root,
            finding,
        ):
            adjudicated.append(finding)
        else:
            rejected.append(finding)
    personal_findings = _find_personal_path_findings(repo_root, candidate_files)
    return SecretScanResult(
        rejected=tuple(sorted(rejected)),
        adjudicated=tuple(sorted(adjudicated)),
        personal_findings=tuple(personal_findings),
    )


def _is_adjudicated_checksum(
    snapshot_root: Path,
    finding: SecretFinding,
) -> bool:
    return _is_approved_secret(snapshot_root, finding)


def _parse_git_tree_entries(payload: bytes) -> list[GitTreeEntry]:
    entries: list[GitTreeEntry] = []
    seen_paths: set[str] = set()
    portable_paths: dict[str, str] = {}
    for raw_entry in payload.split(b"\0"):
        if not raw_entry:
            continue
        metadata, separator, raw_path = raw_entry.partition(b"\t")
        fields = metadata.split(b" ")
        if separator != b"\t" or len(fields) != 3 or not raw_path:
            raise RuntimeError("Git devolvió un inventario histórico no válido")
        try:
            mode = fields[0].decode("ascii", errors="strict")
            object_type = fields[1].decode("ascii", errors="strict")
            object_id = fields[2].decode("ascii", errors="strict")
            path = raw_path.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise RuntimeError(
                "el historial contiene metadatos que no son UTF-8"
            ) from error
        pure_path = PurePosixPath(path)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or path != pure_path.as_posix()
        ):
            raise RuntimeError("el historial contiene una ruta insegura")
        if path in seen_paths:
            raise RuntimeError("el historial contiene una ruta duplicada")
        seen_paths.add(path)
        portable_path = unicodedata.normalize("NFD", path).casefold()
        if portable_path in portable_paths:
            raise RuntimeError(
                "el historial contiene una colisión Unicode o de mayúsculas"
            )
        portable_paths[portable_path] = path
        if mode == "120000":
            raise RuntimeError("el historial contiene un enlace simbólico")
        if mode == "160000" or object_type == "commit":
            raise RuntimeError("el historial contiene un gitlink")
        if mode not in {"100644", "100755"} or object_type != "blob":
            raise RuntimeError("el historial contiene un modo no permitido")
        if re.fullmatch(r"[0-9a-f]{40,64}", object_id) is None:
            raise RuntimeError("el historial contiene un objeto no válido")
        entries.append(GitTreeEntry(path, object_id, mode))
    return entries


def _materialize_commit(
    repo_root: Path,
    commit: str,
    snapshot_root: Path,
) -> list[Path]:
    inventory = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", commit],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if inventory.returncode != 0:
        raise RuntimeError("Git no pudo inventariar un commit")
    entries = _parse_git_tree_entries(inventory.stdout)
    candidates: list[Path] = []
    for entry in entries:
        completed = subprocess.run(
            ["git", "cat-file", "blob", entry.object_id],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError("Git no pudo leer un blob histórico")
        destination = snapshot_root / entry.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(completed.stdout)
        candidates.append(destination)
    return candidates


def _git_commits(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("Git no pudo enumerar el historial")
    try:
        commits = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError("Git devolvió identificadores no válidos") from error
    if not commits or any(
        re.fullmatch(r"[0-9a-f]{40,64}", commit) is None for commit in commits
    ):
        raise RuntimeError("Git devolvió un historial no válido")
    return commits


def _git_index_tree(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "write-tree"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("Git no pudo materializar el índice")
    try:
        tree_id = completed.stdout.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise RuntimeError("Git devolvió un índice no válido") from error
    if re.fullmatch(r"[0-9a-f]{40,64}", tree_id) is None:
        raise RuntimeError("Git devolvió un índice no válido")
    return tree_id


def scan_git_index(repo_root: Path) -> SecretScanResult:
    tree_id = _git_index_tree(repo_root)
    with tempfile.TemporaryDirectory(prefix="easy_ml_index_") as directory:
        snapshot_root = Path(directory) / "snapshot"
        snapshot_root.mkdir()
        candidates = _materialize_commit(repo_root, tree_id, snapshot_root)
        return scan_security_snapshot(snapshot_root, candidates)


def scan_git_history(repo_root: Path) -> list[HistoricalFinding]:
    adjudicated: list[HistoricalFinding] = []
    rejected: list[HistoricalFinding] = []
    for commit in _git_commits(repo_root):
        with tempfile.TemporaryDirectory(prefix="easy_ml_history_") as directory:
            snapshot_root = Path(directory) / "snapshot"
            snapshot_root.mkdir()
            candidates = _materialize_commit(repo_root, commit, snapshot_root)
            result = scan_security_snapshot(snapshot_root, candidates)
            for finding in result.adjudicated:
                historical_finding = HistoricalFinding(
                    commit=commit,
                    path=finding.path,
                    line_number=finding.line_number,
                    detector_type=finding.detector_type,
                )
                adjudicated.append(historical_finding)
            for finding in [*result.rejected, *result.personal_findings]:
                rejected.append(
                    HistoricalFinding(
                        commit=commit,
                        path=finding.path,
                        line_number=finding.line_number,
                        detector_type=finding.detector_type,
                    )
                )
    if rejected:
        raise HistoricalScanError(rejected)
    return sorted(adjudicated)


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
            stderr=subprocess.PIPE,
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
            capture_output=True,
        )


def main() -> int:
    try:
        current_result = scan_security_snapshot(REPO_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: ESCANEO_SECRETOS", file=sys.stderr)
        return 2
    try:
        index_result = scan_git_index(REPO_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: INDICE_GIT", file=sys.stderr)
        return 2
    try:
        historical_findings = scan_git_history(REPO_ROOT)
    except HistoricalScanError as error:
        for line in render_historical_findings(error.findings):
            print(f"HALLAZGO_HISTORICO: {line}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR_SEGURIDAD: HISTORIAL_GIT", file=sys.stderr)
        return 2
    if current_result.rejected:
        for line in render_secret_findings(list(current_result.rejected)):
            print(f"POTENCIAL_SECRETO: {line}", file=sys.stderr)
    if index_result.rejected:
        for line in render_secret_findings(list(index_result.rejected)):
            print(f"POTENCIAL_SECRETO_INDICE: {line}", file=sys.stderr)
    for prefix, personal_findings in (
        ("RUTA_PERSONAL", current_result.personal_findings),
        ("RUTA_PERSONAL_INDICE", index_result.personal_findings),
    ):
        for finding in personal_findings:
            print(
                f"{prefix}: {_escape_metadata(finding.path)}",
                file=sys.stderr,
            )
    if (
        current_result.rejected
        or index_result.rejected
        or current_result.personal_findings
        or index_result.personal_findings
    ):
        return 1
    try:
        run_dependency_audit(BOOK_ROOT)
    except Exception:
        print("ERROR_SEGURIDAD: AUDITORIA_DEPENDENCIAS", file=sys.stderr)
        return 2
    print(
        "SUPRESIONES_ADJUDICADAS "
        f"actual={len(current_result.adjudicated)} "
        f"indice={len(index_result.adjudicated)} "
        f"historial={len(historical_findings)}"
    )
    print("SEGURIDAD_PUBLICACION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
