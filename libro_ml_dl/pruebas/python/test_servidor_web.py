from __future__ import annotations

import http.client
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.servidor_web import create_server


class SecureWebServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.book_root = Path(self.temporary_directory.name) / "libro_ml_dl"
        self._write("index.html", b"home")
        self._write("contenido/01_datos_y_formas/index.html", b"module")
        self._write("assets/css/estilos.css", b"body{}")
        self._write("assets/js/app.mjs", b"export {}")
        self._write("assets/vendor/pyodide/pyodide.mjs", b"export {}")
        self._write(".venv/pyvenv.cfg", b"private")
        self._write("scripts/lanzar.py", b"private")
        self._write("configuracion/local.json", b"private")
        self._write("contenido_fuente/00_inicio/index.md", b"private")
        self._write("uv.lock", b"private")
        self.server = create_server(self.book_root, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def _write(self, relative_path: str, content: bytes) -> Path:
        path = self.book_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def _request(
        self,
        path: str,
        *,
        method: str = "GET",
        host: str | None = None,
    ) -> tuple[int, bytes, dict[str, str]]:
        port = self.server.server_port
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request(
            method,
            path,
            headers={"Host": host or f"127.0.0.1:{port}"},
        )
        response = connection.getresponse()
        body = response.read()
        headers = {name.lower(): value for name, value in response.getheaders()}
        connection.close()
        return response.status, body, headers

    def test_get_and_head_serve_only_required_public_files(self) -> None:
        expected_bodies = {
            "/": b"home",
            "/index.html": b"home",
            "/contenido/01_datos_y_formas/index.html": b"module",
            "/assets/css/estilos.css": b"body{}",
            "/assets/js/app.mjs": b"export {}",
            "/assets/vendor/pyodide/pyodide.mjs": b"export {}",
        }
        for route, expected_body in expected_bodies.items():
            with self.subTest(route=route):
                status, body, headers = self._request(route)
                self.assertEqual(status, 200)
                self.assertEqual(body, expected_body)
                self.assertEqual(headers["x-content-type-options"], "nosniff")

                status, body, headers = self._request(route, method="HEAD")
                self.assertEqual(status, 200)
                self.assertEqual(body, b"")
                self.assertEqual(int(headers["content-length"]), len(expected_body))

    def test_private_directories_dotfiles_and_listings_are_not_served(self) -> None:
        for route in (
            "/.venv/pyvenv.cfg",
            "/scripts/lanzar.py",
            "/configuracion/local.json",
            "/contenido_fuente/00_inicio/index.md",
            "/uv.lock",
            "/.gitignore",
            "/assets/js/",
            "/contenido/",
            "/%2e%2e/README.md",
        ):
            with self.subTest(route=route):
                status, _body, _headers = self._request(route)
                self.assertNotEqual(status, 200)

    def test_runtime_prefix_rejects_symlinks(self) -> None:
        outside = Path(self.temporary_directory.name) / "outside.mjs"
        outside.write_bytes(b"private")
        link = self.book_root / "assets/vendor/pyodide/linked.mjs"
        link.symlink_to(outside)

        status, _body, _headers = self._request("/assets/vendor/pyodide/linked.mjs")

        self.assertNotEqual(status, 200)

    def test_host_must_be_loopback_with_the_actual_port(self) -> None:
        port = self.server.server_port
        for host in (
            "attacker.example",
            "127.0.0.1",
            f"127.0.0.1:{port + 1}",
            f"localhost:{port}@attacker.example",
        ):
            with self.subTest(host=host):
                status, _body, _headers = self._request("/", host=host)
                self.assertNotEqual(status, 200)

        for host in (
            f"127.0.0.1:{port}",
            f"localhost:{port}",
            f"[::1]:{port}",
        ):
            with self.subTest(host=host):
                status, body, _headers = self._request("/", host=host)
                self.assertEqual(status, 200)
                self.assertEqual(body, b"home")


if __name__ == "__main__":
    unittest.main()
