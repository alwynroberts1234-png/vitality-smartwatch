"""Project-local SDK setup. Host Python/Git tools are supplied by the shell entry point."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]
REVISION="v4.1.0"


def python_path(folder, platform=sys.platform):
    return folder/("Scripts/python.exe" if platform=="win32" else "bin/python")


def run(command, **kwargs):
    print("+ "+shlex.join([str(x) for x in command]), flush=True)
    return subprocess.run([str(x) for x in command], check=True, **kwargs)


def load_state(root=ROOT):
    try:
        return json.loads((root/".tools"/"environment.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def saved_environment(state, environ=None):
    env=dict(os.environ if environ is None else environ)
    env["PATH"]=os.pathsep.join(state.get("path_entries",[])+[env.get("PATH","")])
    env["ZEPHYR_BASE"]=str(Path(state["workspace"])/"zephyr")
    env["ZEPHYR_SDK_INSTALL_DIR"]=state["sdk"]
    env["ZEPHYR_TOOLCHAIN_VARIANT"]="zephyr"
    return env


def compiler_path(sdk):
    return sdk/"arm-zephyr-eabi"/"bin"/("arm-zephyr-eabi-gcc.exe" if os.name=="nt" else "arm-zephyr-eabi-gcc")


def state_ready(state, root=ROOT):
    if state.get("schema")!=1 or state.get("revision")!=REVISION or state.get("root")!=str(root):
        return False
    try:
        requested=os.environ.get("VITALITY_ZEPHYR_WORKSPACE")
        if requested and Path(requested).expanduser().resolve()!=Path(state["workspace"]):
            return False
        needed=(state["python"],state["compiler"],
                str(Path(state["workspace"])/".west"/"config"),
                str(Path(state["workspace"])/"zephyr"/"CMakeLists.txt"))
        if not all(Path(p).is_file() for p in needed):
            return False
        env=saved_environment(state)
        if not all(shutil.which(tool,path=env["PATH"]) for tool in ("git","cmake","ninja","gperf","dtc")):
            return False
        return subprocess.run([state["python"],"-m","west","--version"],env=env,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
    except (OSError,KeyError):
        return False


def verify_zephyr(base):
    version=base/"VERSION"
    if not version.is_file():
        raise RuntimeError("Zephyr VERSION file is missing: "+str(version))
    values={}
    for line in version.read_text().splitlines():
        if "=" in line:
            key,value=line.split("=",1)
            values[key.strip()]=value.strip()
    if tuple(values.get(k) for k in ("VERSION_MAJOR","VERSION_MINOR","PATCHLEVEL"))!=("4","1","0"):
        raise RuntimeError("Existing workspace is not Zephyr 4.1.0; it will not be modified.")


def locate_sdk(py, local, base, env):
    expected=(base/"SDK_VERSION").read_text().strip()
    candidates=[local/"zephyr-sdk"]
    if env.get("ZEPHYR_SDK_INSTALL_DIR"):
        candidates.append(Path(env["ZEPHYR_SDK_INSTALL_DIR"]))
    listing=subprocess.run([str(py),"-m","west","sdk","list"],cwd=base,env=env,
                           capture_output=True,text=True)
    for line in listing.stdout.splitlines():
        match=re.search(r"path:\s*(.+)",line)
        if match:
            candidates.append(Path(match.group(1).strip()))
    for sdk in candidates:
        version=sdk/"sdk_version"
        if version.is_file() and version.read_text().strip()==expected and compiler_path(sdk).is_file():
            return sdk
    return None


def setup(root=ROOT):
    state=load_state(root)
    if state_ready(state,root):
        print("Development environment ready; reusing installed tools.",flush=True)
        return state
    local=root/".tools"
    local.mkdir(exist_ok=True)
    py=python_path(local/"venv")
    if not py.is_file():
        venv.EnvBuilder(with_pip=True).create(local/"venv")
    env=dict(os.environ)
    env["PATH"]=str(py.parent)+os.pathsep+env.get("PATH","")
    run([py,"-m","pip","install","west>=1.2,<2","cmake>=3.20.5,<4","ninja>=1.11,<2"],env=env)
    workspace=Path(env.get("VITALITY_ZEPHYR_WORKSPACE") or root.parent/"zephyr-workspace").expanduser()
    if not (workspace/".west").is_dir():
        if env.get("VITALITY_ZEPHYR_WORKSPACE"):
            raise RuntimeError("Configured workspace is missing: "+str(workspace))
        workspace=local/"zephyr-workspace"
        if not (workspace/".west").is_dir():
            if workspace.exists() and any(workspace.iterdir()):
                raise RuntimeError("Nonempty incomplete workspace: "+str(workspace)+". Inspect it before retrying.")
            run([py,"-m","west","init","-m","https://github.com/zephyrproject-rtos/zephyr",
                 "--mr",REVISION,workspace],env=env,cwd=root)
    workspace=workspace.resolve()
    base=workspace/"zephyr"
    verify_zephyr(base)
    env["ZEPHYR_BASE"]=str(base)
    run([py,"-m","west","update","--narrow"],cwd=workspace,env=env)
    run([py,"-m","west","zephyr-export"],cwd=workspace,env=env)
    run([py,"-m","west","packages","pip","--install"],cwd=workspace,env=env)
    sdk=locate_sdk(py,local,base,env)
    if sdk is None:
        run([py,"-m","west","sdk","install","--install-dir",local/"zephyr-sdk",
             "--toolchains","arm-zephyr-eabi"],cwd=base,env=env)
        sdk=locate_sdk(py,local,base,env)
    if sdk is None:
        raise RuntimeError("SDK installation did not provide the required ARM compiler.")
    compiler=compiler_path(sdk)
    run([compiler,"--version"],env=env)
    state={"schema":1,"root":str(root),"revision":REVISION,"python":str(py),
           "workspace":str(workspace),"sdk":str(sdk),"compiler":str(compiler),
           "path_entries":list(dict.fromkeys([str(py.parent)]+env["PATH"].split(os.pathsep)))}
    temporary=local/"environment.json.tmp"
    temporary.write_text(json.dumps(state,indent=2),encoding="utf-8")
    temporary.replace(local/"environment.json")
    print("Development environment ready.",flush=True)
    return state


def start_project(state,root=ROOT):
    env=saved_environment(state)
    preview_error=False
    if os.name=="nt":
        try:
            run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",
                 root/"tools"/"Build-Preview.ps1","-Run"],cwd=root,env=env)
        except subprocess.CalledProcessError:
            preview_error=True
            print("Preview failed; continuing with firmware build.",file=sys.stderr)
    else:
        (root/"build").mkdir(exist_ok=True)
        with (root/"build"/"portable-preview.log").open("ab") as log:
            child=subprocess.Popen([state["python"],str(root/"preview"/"watch_preview.py")],
                cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        try:
            if child.wait(timeout=1):
                preview_error=True
                print("Preview failed; see build/portable-preview.log.",file=sys.stderr)
        except subprocess.TimeoutExpired:
            pass
    result=subprocess.run([state["python"],str(root/"tools"/"dev.py"),"firmware",
                           "--workspace",state["workspace"],"--python",state["python"]],cwd=root,env=env)
    return result.returncode or int(preview_error)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",action="store_true")
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument("--start",action="store_true")
    actions.add_argument("--check",action="store_true")
    actions.add_argument("--launch-only",action="store_true")
    args=parser.parse_args(argv)
    if args.plan:
        print("Plan: create .tools/venv, prepare Zephyr "+REVISION+
              ", install arm-zephyr-eabi, save paths, then launch UI/build.")
        print("No downloads or filesystem changes made.")
        return 0
    try:
        if args.check or args.launch_only:
            state=load_state()
            ready=state_ready(state)
            if args.check:
                print("Saved development environment is ready." if ready else
                      "Development environment needs preparation in the download stage.",flush=True)
                # Missing dependencies are findings, not a failure: stage 3 installs them.
                return 0
            if not ready:
                raise RuntimeError("Environment is not ready. Run Vitality: Open project first.")
            return start_project(state)
        state=setup()
        return start_project(state) if args.start else 0
    except (OSError,RuntimeError,subprocess.CalledProcessError) as error:
        print("SETUP FAILED: "+str(error),file=sys.stderr)
        print("Correct the reported error and rerun Vitality: Open project.",file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__=="__main__":
    raise SystemExit(main())
