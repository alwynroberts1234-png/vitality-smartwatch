"""UI setup checks; never download packages or compile firmware."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StartupTests(unittest.TestCase):
    def test_startup_has_no_firmware_task(self):
        tasks = json.loads((ROOT / ".vscode" / "tasks.json").read_text())["tasks"]
        self.assertEqual(len(tasks), 6)
        self.assertFalse(any("firmware" in json.dumps(task).lower() for task in tasks))
        self.assertFalse((ROOT / "tools" / "setup_env.py").exists())
        for script in ("Setup-Environment.ps1", "setup-host.sh"):
            source = (ROOT / "tools" / script).read_text()
            for installer in ("west init", "west sdk", "pip install", "setup_env.py", "Build-Firmware.ps1"):
                self.assertNotIn(installer, source)

    @unittest.skipUnless(os.name == "nt", "Windows native runtime check")
    def test_windows_check_and_prepare_need_no_download(self):
        for stage in ("Detect", "Check", "Download"):
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(ROOT / "tools" / "Setup-Environment.ps1"), "-Stage", stage],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            if stage == "Download":
                self.assertIn("0 bytes", result.stdout)

    @unittest.skipIf(os.name == "nt", "Native Unix shell checks")
    def test_unix_existing_runtime_reused_and_launches_only_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            shutil.copyfile(ROOT / "tools" / "setup-host.sh", root / "tools" / "setup-host.sh")
            runtime = root / "python with spaces"
            runtime.write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\nprintf "%s\\n" "$@" > "$UI_TEST_LOG"\n')
            runtime.chmod(0o755)
            log = root / "launch.txt"
            env = dict(os.environ, VITALITY_PREVIEW_PYTHON=str(runtime), UI_TEST_LOG=str(log))
            script = ["bash", str(root / "tools" / "setup-host.sh")]
            for stage in ("--detect", "--check", "--download", "--launch"):
                result = subprocess.run(script + [stage], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                if stage == "--check":
                    self.assertFalse((root / ".tools").exists())
                if stage == "--download":
                    self.assertIn("0 bytes", result.stdout)
                    self.assertEqual((root / ".tools" / "preview-python").read_text().strip(), str(runtime))
            self.assertEqual(log.read_text().strip(), str(root / "preview" / "watch_preview.py"))
            self.assertFalse((root / ".tools" / "venv").exists())


if __name__ == "__main__":
    unittest.main()
