"""Helpers for cog'd documentation files."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from inspect import cleandoc
from pathlib import Path

ORIGINAL_DIR = os.getcwd()
ROOT = Path(".")
CUR_TEMP_DIR = None
PRETEND_DIR = ""


def dbgout(msg, **kwargs):
    print(msg, file=sys.stderr, flush=True, **kwargs)


def set_source_root(dirname):
    global ROOT
    ROOT = Path(dirname).resolve()


FILETYPES = {
    "py": "python",
    "cfg": "ini",
}


def show_file(fname, *, start=None, end=None):
    fpath = ROOT / fname
    ext = fpath.suffix.strip(".")
    file_type = FILETYPES.get(ext, ext)
    with open(fpath) as f:
        lines = f.read().splitlines(keepends=True)

    if start:
        lineno = next(num for num, line in enumerate(lines) if re.search(start, line))
        lines = lines[lineno:]
    if end:
        lineno = next(num for num, line in enumerate(lines) if re.search(end, line))
        lines = lines[: lineno + 1]

    print(f"```{file_type}")
    print("".join(lines), end="")
    print("```")


def cd_temp(*, pretend=None):
    global CUR_TEMP_DIR, PRETEND_DIR
    CUR_TEMP_DIR = tempfile.TemporaryDirectory(prefix="ickdoc_")
    os.chdir(CUR_TEMP_DIR.name)
    if pretend:
        PRETEND_DIR = pretend


def run_cmd(cmds, **kwargs) -> None:
    for cmd in cleandoc(cmds).splitlines():
        subprocess.run(
            cmd,
            encoding="utf-8",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs,
        )


def show_cmd(cmd, hide_command=False, columns=None, **kwargs) -> None:
    env = dict(os.environ)
    env["COLUMNS"] = str(columns or 999)
    proc = subprocess.run(
        cmd,
        encoding="utf-8",
        shell=True,
        check=False,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )
    output = proc.stdout
    output = re.sub(pattern=r"(?m) +$", repl="", string=output)
    if PRETEND_DIR:
        actual_temp = Path(CUR_TEMP_DIR.name).resolve()
        output = output.replace(str(actual_temp), PRETEND_DIR)
    print("```shell")
    if not hide_command:
        print(f"$ {cmd}")
    print(output, end="")
    if proc.returncode != 0:
        print(f"(exited with {proc.returncode})")
    print("```")


def copy_file(fname, dst_name=None, *, show=False):
    dst = Path(dst_name or fname)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / fname, dst)
    if show:
        show_file(fname)


def copy_tree(dname, dst_name=None):
    dst = Path(dst_name or dname)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / dname, dst)


def pause(msg=""):
    dbgout(f"Currently in {os.getcwd()}")
    if msg:
        dbgout(msg)
    dbgout("waiting > ", end="")
    input()
