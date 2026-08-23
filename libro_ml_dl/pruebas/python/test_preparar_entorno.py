import hashlib
import json
import tarfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.preparar_entorno import (
    CORE_ARCHIVE,
    CORE_REQUIRED_FILES,
    CORE_SHA256,
    CORE_URL,
    PYODIDE_VERSION,
    REQUIRED_PACKAGES,
    download_verified,
    prepare_runtime,
    resolve_package_closure,
    sha256_file,
)


class PyodidePreparationTests(unittest.TestCase):
    def _sha256_bytes(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _write_core_archive(
        self,
        root: Path,
    ) -> tuple[Path, dict[str, bytes]]:
        archive_root = root / "archive_root"
        pyodide_dir = archive_root / "pyodide"
        pyodide_dir.mkdir(parents=True)
        package_contents = {
            f"{package_name}.data": package_name.encode("utf-8")
            for package_name in REQUIRED_PACKAGES
        }
        lock_data = {
            "packages": {
                package_name: {
                    "depends": [],
                    "file_name": f"{package_name}.data",
                    "sha256": self._sha256_bytes(
                        package_contents[f"{package_name}.data"]
                    ),
                }
                for package_name in REQUIRED_PACKAGES
            }
        }
        for file_name in CORE_REQUIRED_FILES:
            if file_name != "pyodide-lock.json":
                (pyodide_dir / file_name).write_bytes(file_name.encode("utf-8"))
        (pyodide_dir / "pyodide-lock.json").write_text(
            json.dumps(lock_data),
            encoding="utf-8",
        )
        archive_path = root / "core.tar.bz2"
        with tarfile.open(archive_path, mode="w:bz2") as archive:
            archive.add(pyodide_dir, arcname="pyodide")
        return archive_path, package_contents

    def test_resolves_transitive_dependencies_in_stable_order(self) -> None:
        lock_data = {
            "packages": {
                "pandas": {"depends": ["numpy", "pytz"]},
                "numpy": {"depends": []},
                "pytz": {"depends": []},
            }
        }
        self.assertEqual(
            resolve_package_closure(lock_data, ("pandas",)),
            ["numpy", "pytz", "pandas"],
        )

    def test_sha256_file_uses_file_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"abc")
            self.assertEqual(
                sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",  # pragma: allowlist secret  # noqa: E501
            )

    def test_bad_download_hash_never_publishes_target(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            target = root / "target.bin"
            source.write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError, "hash inválido"):
                download_verified(source.as_uri(), target, "0" * 64)
            self.assertFalse(target.exists())

    def test_rejects_existing_runtime_with_incomplete_manifest(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path, package_contents = self._write_core_archive(root)
            vendor_dir = root / "vendor" / "pyodide"
            with tarfile.open(archive_path, mode="r:bz2") as archive:
                archive.extractall(vendor_dir.parent, filter="data")
            file_hashes = {
                path.name: sha256_file(path)
                for path in vendor_dir.iterdir()
                if path.is_file()
            }
            for file_name, content in package_contents.items():
                path = vendor_dir / file_name
                path.write_bytes(content)
                file_hashes[file_name] = sha256_file(path)
            file_hashes.pop("numpy.data")
            manifest = {
                "schema_version": 1,
                "pyodide_version": PYODIDE_VERSION,
                "core_archive": CORE_ARCHIVE,
                "core_sha256": CORE_SHA256,
                "requested_packages": list(REQUIRED_PACKAGES),
                "package_closure": list(REQUIRED_PACKAGES),
                "file_hashes": file_hashes,
            }
            (vendor_dir / "manifest.local.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            with self.assertRaises(RuntimeError):
                prepare_runtime(vendor_dir)

    def test_failed_package_download_keeps_vendor_directory_retryable(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path, package_contents = self._write_core_archive(root)
            vendor_dir = root / "vendor" / "pyodide"
            vendor_dir.mkdir(parents=True)
            (vendor_dir / ".gitkeep").touch()

            def download_core_then_fail(
                url: str,
                target: Path,
                expected_sha256: str,
            ) -> None:
                del expected_sha256
                if url == CORE_URL:
                    target.write_bytes(archive_path.read_bytes())
                    return
                raise RuntimeError("fallo simulado de paquete")

            with patch(
                "scripts.preparar_entorno.download_verified",
                side_effect=download_core_then_fail,
            ):
                with self.assertRaisesRegex(RuntimeError, "fallo simulado"):
                    prepare_runtime(vendor_dir)

            self.assertEqual([path.name for path in vendor_dir.iterdir()], [".gitkeep"])

            def download_successfully(
                url: str,
                target: Path,
                expected_sha256: str,
            ) -> None:
                del expected_sha256
                content = (
                    archive_path.read_bytes()
                    if url == CORE_URL
                    else package_contents[target.name]
                )
                target.write_bytes(content)

            with patch(
                "scripts.preparar_entorno.download_verified",
                side_effect=download_successfully,
            ):
                manifest = prepare_runtime(vendor_dir)

            self.assertEqual(manifest["package_closure"], list(REQUIRED_PACKAGES))
            self.assertTrue((vendor_dir / ".gitkeep").is_file())
            self.assertTrue((vendor_dir / "manifest.local.json").is_file())
