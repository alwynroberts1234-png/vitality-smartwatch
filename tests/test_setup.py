"""Bootstrap regression checks. Never install packages or download an SDK."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import setup_env as setup
import dev


class SetupTests(unittest.TestCase):
    def test_check_reports_missing_environment_without_installing(self):
        with patch.object(setup, "load_state", return_value={}), \
             patch.object(setup, "state_ready", return_value=False), \
             patch.object(setup, "setup") as install, \
             patch.object(setup, "start_project") as launch:
            self.assertEqual(setup.main(["--check"]), 0)
            install.assert_not_called()
            launch.assert_not_called()

    def test_launch_requires_ready_environment_and_never_installs(self):
        state={"cached": True}
        with patch.object(setup, "load_state", return_value=state), \
             patch.object(setup, "state_ready", return_value=False) as ready, \
             patch.object(setup, "setup") as install, \
             patch.object(setup, "start_project", return_value=7) as launch:
            self.assertEqual(setup.main(["--launch-only"]), 1)
            launch.assert_not_called()
            ready.return_value=True
            self.assertEqual(setup.main(["--launch-only"]), 7)
            launch.assert_called_once_with(state)
            install.assert_not_called()

    def test_plan_has_no_side_effects(self):
        with patch.object(setup, "setup") as install:
            self.assertEqual(setup.main(["--plan", "--start"]), 0)
            install.assert_not_called()

    def test_cached_setup_does_not_download(self):
        with patch.object(setup, "load_state", return_value={"cached": True}), \
             patch.object(setup, "state_ready", return_value=True), \
             patch.object(setup, "run") as command:
            self.assertEqual(setup.setup(), {"cached": True})
            command.assert_not_called()

    def test_failed_install_does_not_save_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            py = setup.python_path(root / ".tools" / "venv")
            py.parent.mkdir(parents=True)
            py.touch()
            with patch.object(setup, "run", side_effect=subprocess.CalledProcessError(1, ["pip"])):
                with self.assertRaises(subprocess.CalledProcessError):
                    setup.setup(root)
            self.assertFalse((root / ".tools" / "environment.json").exists())

    def test_incompatible_workspace_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "VERSION").write_text("VERSION_MAJOR = 4\nVERSION_MINOR = 2\nPATCHLEVEL = 0\n")
            with self.assertRaisesRegex(RuntimeError, "will not be modified"):
                setup.verify_zephyr(base)

    def test_fresh_setup_order_and_saved_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project with spaces"
            root.mkdir()
            local = root / ".tools"
            py = setup.python_path(local / "venv")
            sdk = local / "zephyr-sdk"
            commands = []

            def create_venv(folder):
                py.parent.mkdir(parents=True)
                py.touch()

            def command(argv, **kwargs):
                argv = [str(item) for item in argv]
                commands.append(argv)
                self.assertNotIn("shell", kwargs)
                if "init" in argv:
                    workspace = Path(argv[-1])
                    (workspace / ".west").mkdir(parents=True)
                    (workspace / ".west" / "config").touch()
                    base = workspace / "zephyr"
                    base.mkdir()
                    (base / "CMakeLists.txt").touch()
                    (base / "VERSION").write_text("VERSION_MAJOR = 4\nVERSION_MINOR = 1\nPATCHLEVEL = 0\n")
                if "sdk" in argv:
                    compiler = setup.compiler_path(sdk)
                    compiler.parent.mkdir(parents=True)
                    compiler.touch()
                return subprocess.CompletedProcess(argv, 0)

            with patch.dict(os.environ, {}, clear=True), \
                 patch.object(setup.venv.EnvBuilder, "create", side_effect=create_venv), \
                 patch.object(setup, "run", side_effect=command), \
                 patch.object(setup, "locate_sdk", side_effect=[None, sdk]):
                state = setup.setup(root)
            self.assertEqual([argv[3] for argv in commands[:-1]],
                             ["install", "init", "update", "zephyr-export", "packages", "sdk"])
            self.assertIn("v4.1.0", commands[1])
            self.assertEqual(commands[-2][-2:], ["--toolchains", "arm-zephyr-eabi"])
            self.assertEqual(setup.load_state(root), state)
            self.assertEqual(state["python"], str(py))
            self.assertEqual(state["workspace"], str((local / "zephyr-workspace").resolve()))

    def test_sdk_selection_checks_version_and_arm_compiler(self):
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp)
            base = local / "zephyr"
            base.mkdir()
            (base / "SDK_VERSION").write_text("0.17.0\n")
            sdk = local / "registered sdk"
            compiler = setup.compiler_path(sdk)
            compiler.parent.mkdir(parents=True)
            compiler.touch()
            (sdk / "sdk_version").write_text("0.17.0")
            listing = subprocess.CompletedProcess([], 0, stdout="  path: " + str(sdk) + "\n")
            with patch.object(setup.subprocess, "run", return_value=listing):
                self.assertEqual(setup.locate_sdk(Path(sys.executable), local, base, {}), sdk)
                (sdk / "sdk_version").write_text("0.16.0")
                self.assertIsNone(setup.locate_sdk(Path(sys.executable), local, base, {}))

    def test_manual_build_uses_saved_paths_and_explicit_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace with spaces"
            (workspace / ".west").mkdir(parents=True)
            (workspace / "zephyr").mkdir()
            (workspace / "zephyr" / "CMakeLists.txt").touch()
            (root / ".tools").mkdir()
            state = {"root": str(root), "python": sys.executable, "workspace": str(workspace),
                     "sdk": "saved-sdk", "path_entries": ["saved-tools"]}
            (root / ".tools" / "environment.json").write_text(json.dumps(state))
            args = argparse.Namespace(workspace=None, python=None)
            ws, py, env = dev.firmware_config(args, root, {})
            self.assertEqual(ws, workspace.resolve())
            self.assertEqual(py, Path(sys.executable))
            self.assertIn("saved-tools", env["PATH"])
            self.assertEqual(env["ZEPHYR_SDK_INSTALL_DIR"], "saved-sdk")
            _, _, env = dev.firmware_config(args, root, {"ZEPHYR_SDK_INSTALL_DIR": "custom-sdk"})
            self.assertEqual(env["ZEPHYR_SDK_INSTALL_DIR"], "custom-sdk")

    def test_start_only_after_setup_succeeds(self):
        with patch.object(setup, "setup", side_effect=RuntimeError("missing prerequisite")), \
             patch.object(setup, "start_project") as start:
            self.assertEqual(setup.main(["--start"]), 1)
            start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
