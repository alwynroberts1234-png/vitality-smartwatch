"""Cross-platform launcher and preview regression tests; no Zephyr SDK needed."""
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
def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
dev=load("vitality_dev",ROOT/"tools"/"dev.py")
preview=load("portable_watch",ROOT/"preview"/"watch_preview.py")


class LauncherTests(unittest.TestCase):
    def test_tasks_for_each_os(self):
        data=json.loads((ROOT/".vscode"/"tasks.json").read_text())
        auto=data["tasks"][0]
        self.assertEqual(auto["runOptions"]["runOn"],"folderOpen")
        self.assertEqual(auto["dependsOrder"], "sequence")
        stages=data["tasks"][1:5]
        self.assertEqual(auto["dependsOn"], [task["label"] for task in stages])
        for task, flag, stage in zip(stages, ("--detect", "--check", "--download", "--launch"),
                                     ("Detect", "Check", "Download", "Launch")):
            self.assertEqual(task["args"], ["${workspaceFolder}/tools/setup-host.sh", flag])
            self.assertEqual(task["windows"]["args"][-2:], ["-Stage", stage])
            self.assertNotIn("runOptions", task)
        for task in data["tasks"][1:]:
            self.assertEqual(task["windows"]["command"],"powershell.exe")
            for os_name in ("linux","osx"):
                self.assertEqual(task.get(os_name, {}).get("command", task["command"]), "bash")
                expected="setup-host.sh" if task in stages else "run-dev.sh"
                self.assertEqual(task["args"][0],"${workspaceFolder}/tools/"+expected)

    def test_venv_layouts(self):
        folder=Path("example")
        self.assertEqual(dev.venv_python(folder,"win32"),folder/"Scripts"/"python.exe")
        for system in ("linux","darwin"):
            self.assertEqual(dev.venv_python(folder,system),folder/"bin"/"python")

    def setup_workspace(self,tmp):
        root=Path(tmp)/"project with spaces"
        ws=Path(tmp)/"zephyr workspace"
        root.mkdir()
        (ws/".west").mkdir(parents=True)
        (ws/"zephyr").mkdir()
        (ws/"zephyr"/"CMakeLists.txt").write_text("# fixture")
        args=argparse.Namespace(action="firmware",workspace=str(ws),python=sys.executable,
                                board="nrf52840dk/nrf52840",extra_conf=None)
        return root,ws,args

    def test_missing_workspace(self):
        args=argparse.Namespace(workspace="/nonexistent-vitality-workspace",python=sys.executable)
        with self.assertRaisesRegex(RuntimeError,"workspace not found"):
            dev.firmware_config(args)

    def test_successful_build_arguments_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,ws,args=self.setup_workspace(tmp)
            (root/"config").mkdir()
            conf=root/"config"/"demo config.conf"
            conf.write_text("CONFIG_VITALITY_SENSOR_SIMULATOR=n")
            args.extra_conf="config/demo config.conf"
            def run(command,**kwargs):
                self.assertEqual(kwargs["cwd"],ws.resolve())
                self.assertEqual(kwargs["env"]["ZEPHYR_BASE"],str(ws.resolve()/"zephyr"))
                self.assertNotIn("shell",kwargs)
                if "build" in command:
                    self.assertIn(str(root),command)
                    self.assertIn("-DEXTRA_CONF_FILE="+str(conf.resolve()),command)
                    dest=root/"build"/"firmware"/"zephyr"
                    dest.mkdir(parents=True)
                    (dest/"zephyr.elf").write_bytes(b"TEST FIXTURE")
                return subprocess.CompletedProcess(command,0)
            with patch.object(dev.subprocess,"run",side_effect=run),patch.object(dev.shutil,"which",return_value="/available/tool"):
                # Resolve the explicit executable before mocks replace PATH resolution.
                with patch.object(dev,"firmware_config",return_value=(ws.resolve(),Path(sys.executable),dict(os.environ,ZEPHYR_BASE=str(ws.resolve()/"zephyr")))):
                    self.assertEqual(dev.firmware(args,root),0)

    def test_build_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,ws,args=self.setup_workspace(tmp)
            calls=[subprocess.CompletedProcess([],0),subprocess.CompletedProcess([],7)]
            with patch.object(dev.subprocess,"run",side_effect=calls),patch.object(dev.shutil,"which",return_value="/available/tool"),patch.object(dev,"firmware_config",return_value=(ws,Path(sys.executable),dict(os.environ))):
                with self.assertRaisesRegex(RuntimeError,"exit code 7"):
                    dev.firmware(args,root)
            self.assertFalse((root/"build"/"firmware"/"zephyr"/"zephyr.elf").exists())

    def test_no_silent_success_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,ws,args=self.setup_workspace(tmp)
            with patch.object(dev.subprocess,"run",return_value=subprocess.CompletedProcess([],0)),patch.object(dev.shutil,"which",return_value="/available/tool"),patch.object(dev,"firmware_config",return_value=(ws,Path(sys.executable),dict(os.environ))):
                with self.assertRaisesRegex(RuntimeError,"without output"):
                    dev.firmware(args,root)


class Canvas:
    """Records drawing calls without a desktop or Tk installation."""
    def __init__(self):
        self.calls=[]
    def __getattr__(self,name):
        def draw(*args,**kwargs):
            if name=="delete":
                self.calls.clear()
            else:
                self.calls.append((name,args,kwargs))
        return draw


class PreviewTests(unittest.TestCase):
    def test_source_themes(self):
        themes=preview.load_themes()
        self.assertEqual(len(themes),6)
        self.assertEqual(themes[2]["name"],"Clinical")

    def test_navigation_measurement_and_sleep(self):
        m=preview.Model()
        m.navigate(-1)
        self.assertEqual(m.screen,5)
        m.navigate(1)
        self.assertEqual(m.screen,0)
        m.measure()
        self.assertEqual(m.remaining,10)
        for _ in range(51):
            m.tick(.2)
        self.assertEqual(m.remaining,0)
        m.sleeping=True
        before=m.elapsed
        m.tick(.1)
        self.assertEqual(m.elapsed,before)
        m.set_simulated(False)
        m.measure()
        self.assertEqual(m.remaining,0)

    def test_animation_and_missing_sensor_rendering(self):
        ui=preview.Preview.__new__(preview.Preview)
        ui.model=preview.Model()
        ui.model.live_clock=False
        ui.themes=preview.load_themes()
        ui.canvas=Canvas()
        for theme in range(6):
            ui.model.theme=theme
            for screen in range(6):
                ui.model.screen=screen
                ui.model.elapsed=2
                ui.draw()
                first=list(ui.canvas.calls)
                ui.model.elapsed=2.24
                ui.draw()
                self.assertNotEqual(first,ui.canvas.calls,(theme,screen))
        ui.model.screen=2
        ui.model.set_simulated(False)
        ui.draw()
        self.assertFalse(any(name=="create_line" and kw.get("fill")=="#ff4975" for name,args,kw in ui.canvas.calls))
        ui.model.sleeping=True
        ui.draw()
        first=list(ui.canvas.calls)
        ui.model.elapsed+=1
        ui.draw()
        self.assertEqual(first,ui.canvas.calls)

    def test_duplicate_instance_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"preview.lock"
            first=preview.InstanceLock(path)
            second=preview.InstanceLock(path)
            self.assertTrue(first.acquire())
            try:
                self.assertFalse(second.acquire())
            finally:
                first.close()
            self.assertTrue(second.acquire())
            second.close()


if __name__=="__main__":
    unittest.main()
