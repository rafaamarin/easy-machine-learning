import json
import os
import signal
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from scripts.lanzar import (
    build_jupyter_command,
    find_free_port,
    find_jupyter_executable,
    main,
    resolve_vault_root,
    stop_processes,
    wait_for_port,
)


class LauncherTests(unittest.TestCase):
    def test_launcher_copy_has_no_unir_specific_kernel_names(self) -> None:
        book_root = Path(__file__).resolve().parents[2]
        source = (book_root / "scripts/lanzar.py").read_text(encoding="utf-8")
        self.assertNotIn("unir-tf", source)
        self.assertNotIn("unir-torch", source)

    def test_find_free_port_skips_occupied_preferred_port(self) -> None:
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", 0))
            port = occupied.getsockname()[1]
            self.assertNotEqual(find_free_port(port), port)

    def test_find_free_port_rejects_values_outside_tcp_range(self) -> None:
        for port in (0, -1, 65536):
            with self.subTest(port=port):
                with self.assertRaisesRegex(ValueError, "1 y 65535"):
                    find_free_port(port)

    def test_find_free_port_stops_at_tcp_upper_boundary(self) -> None:
        with socket.socket() as occupied:
            try:
                occupied.bind(("127.0.0.1", 65535))
            except OSError:
                self.skipTest("El puerto 65535 no está disponible para esta prueba")
            occupied.listen()
            with self.assertRaisesRegex(RuntimeError, "65535 y 65535"):
                find_free_port(65535)

    def test_cli_rejects_invalid_port_with_argparse_error(self) -> None:
        book_root = Path(__file__).resolve().parents[2]
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/lanzar.py",
                "--sin-jupyter",
                "--sin-navegador",
                "--puerto-web",
                "-1",
            ],
            cwd=book_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("puerto debe estar entre 1 y 65535", completed.stderr)

    def test_jupyter_command_is_local_and_uses_ephemeral_token(self) -> None:
        command = build_jupyter_command(
            Path("/tmp/jupyter"),
            port=8890,
            token="test-token",
            repo_root=Path("/tmp/repo"),
        )
        self.assertEqual(command[:2], ["/tmp/jupyter", "lab"])
        self.assertIn("--ServerApp.ip=127.0.0.1", command)
        self.assertIn("--ServerApp.port=8890", command)
        self.assertIn("--ServerApp.token=test-token", command)
        self.assertIn("--ServerApp.root_dir=/tmp/repo", command)
        self.assertIn("--ServerApp.port_retries=0", command)
        self.assertNotIn("--allow-root", command)

    def test_public_project_jupyter_is_selected_while_vault_is_served(self) -> None:
        book_root = Path(__file__).resolve().parents[2]
        vault_root = Path("/tmp/vault")
        project_jupyter = book_root / ".venv" / "bin" / "jupyter"
        processes = [Mock(), Mock()]
        for process in processes:
            process.poll.return_value = 0

        with (
            patch.object(
                sys,
                "argv",
                ["lanzar.py", "--sin-navegador"],
            ),
            patch(
                "scripts.lanzar.resolve_vault_root",
                return_value=vault_root,
            ),
            patch(
                "scripts.lanzar.find_jupyter_executable",
                return_value=project_jupyter,
            ) as find_jupyter,
            patch(
                "scripts.lanzar.find_free_port",
                side_effect=[8000, 8888],
            ),
            patch("scripts.lanzar.wait_for_port"),
            patch(
                "scripts.lanzar.kernel_names",
                return_value={"python3"},
            ),
            patch(
                "scripts.lanzar.subprocess.Popen",
                side_effect=processes,
            ) as popen,
            patch("scripts.lanzar.stop_processes"),
        ):
            self.assertEqual(main(), 1)

        find_jupyter.assert_called_once_with(book_root)
        command = popen.call_args_list[1].args[0]
        self.assertEqual(command[0], str(project_jupyter))
        self.assertIn(f"--ServerApp.root_dir={vault_root}", command)

    def test_wait_for_port_observes_a_listening_local_socket(self) -> None:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(1)"],
            )
            try:
                wait_for_port(
                    listener.getsockname()[1],
                    timeout_seconds=1,
                    process=process,
                )
            finally:
                process.kill()
                process.wait(timeout=1)

    def test_wait_for_port_rejects_a_listener_when_spawned_process_exited(
        self,
    ) -> None:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            process = subprocess.Popen(
                [sys.executable, "-c", "raise SystemExit(7)"],
            )
            self.assertEqual(process.wait(timeout=1), 7)
            with self.assertRaisesRegex(RuntimeError, "terminó.*7"):
                wait_for_port(
                    listener.getsockname()[1],
                    timeout_seconds=1,
                    process=process,
                )

    def test_stop_processes_kills_non_cooperative_process_group(self) -> None:
        program = """
import signal
import subprocess
import sys
import time

signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([
    sys.executable,
    "-c",
    "import signal, time; signal.signal(signal.SIGINT, signal.SIG_IGN); "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); print('ready', flush=True); "
    "time.sleep(60)",
], stdout=subprocess.PIPE, text=True)
assert child.stdout is not None
assert child.stdout.readline().strip() == "ready"
print(child.pid, flush=True)
time.sleep(60)
"""
        process = subprocess.Popen(
            [sys.executable, "-c", program],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        group_id = process.pid
        try:
            assert process.stdout is not None
            child_pid = int(process.stdout.readline().strip())

            stop_processes([process])

            self.assertIsNotNone(process.poll())
            deadline = time.monotonic() + 2
            while self._is_running(child_pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(self._is_running(child_pid))
        finally:
            try:
                os.killpg(group_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if process.poll() is None:
                process.wait(timeout=2)
            if process.stdout is not None:
                process.stdout.close()

    def test_stop_processes_keeps_signaling_group_after_leader_exits(self) -> None:
        program = """
import signal
import subprocess
import sys
import time

child = subprocess.Popen([
    sys.executable,
    "-c",
    "import signal, time; signal.signal(signal.SIGINT, signal.SIG_IGN); "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); print('ready', flush=True); "
    "time.sleep(60)",
], stdout=subprocess.PIPE, text=True)
assert child.stdout is not None
assert child.stdout.readline().strip() == "ready"
print(child.pid, flush=True)
signal.signal(signal.SIGINT, lambda _signal, _frame: sys.exit(0))
time.sleep(60)
"""
        process = subprocess.Popen(
            [sys.executable, "-c", program],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        group_id = process.pid
        try:
            assert process.stdout is not None
            child_pid = int(process.stdout.readline().strip())

            stop_processes([process])

            self.assertEqual(process.poll(), 0)
            deadline = time.monotonic() + 2
            while self._is_running(child_pid) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(self._is_running(child_pid))
        finally:
            try:
                os.killpg(group_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if process.poll() is None:
                process.wait(timeout=2)
            if process.stdout is not None:
                process.stdout.close()

    @staticmethod
    def _is_running(pid: int) -> bool:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", "stat="],
            check=False,
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0 and not completed.stdout.strip().startswith(
            "Z"
        )

    def test_absent_jupyter_executable_returns_none(self) -> None:
        with patch("scripts.lanzar.shutil.which", return_value=None):
            self.assertIsNone(find_jupyter_executable(Path("/missing-repo")))

    def test_configured_vault_root_drives_local_jupyter_lookup(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            book_root = root / "libro_ml_dl"
            vault_root = root / "vault"
            jupyter = vault_root / ".venv" / "bin" / "jupyter"
            (book_root / "configuracion").mkdir(parents=True)
            jupyter.parent.mkdir(parents=True)
            jupyter.touch()
            (book_root / "configuracion" / "local.json").write_text(
                json.dumps({"vault_root": str(vault_root)}), encoding="utf-8"
            )

            self.assertEqual(
                find_jupyter_executable(resolve_vault_root(book_root)),
                jupyter,
            )
