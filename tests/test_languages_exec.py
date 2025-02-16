import os
import subprocess
from contextlib import contextmanager

from ick.config import HookConfig
from ick.languages.exec import Language
from ick_protocol import Finished, Modified


def test_smoke_single_file(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = HookConfig(
        name="hello",
        language="exec",
        command="sed -i -e 's/hello/HELLO/'",
    )
    lang = Language(conf, None)
    with lang.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 2
    assert isinstance(resp[0], Modified)
    assert resp[0].filename == "README.md"
    assert resp[0].new_bytes == b"HELLO world\n"
    assert resp[0].diffstat == "+1-1"

    assert isinstance(resp[1], Finished)


def test_smoke_not_found(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = HookConfig(
        name="hello",
        language="exec",
        command="/bin/zzyzx",
    )
    lang = Language(conf, None)
    with lang.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 1
    assert isinstance(resp[0], Finished)
    assert resp[0].error
    assert "No such file or directory: '/bin/zzyzx'" in resp[0].message


def test_smoke_failure(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = HookConfig(
        name="hello",
        language="exec",
        command="/bin/sh -c 'exit 1'",
    )
    lang = Language(conf, None)
    with lang.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 1
    assert isinstance(resp[0], Finished)
    assert resp[0].error
    assert "returned non-zero exit status" in resp[0].message


def test_smoke_repo(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = HookConfig(
        name="hello",
        language="exec",
        scope="repo",
        command="sed -i -e 's/hello/HELLO/' README.md",
    )
    lang = Language(conf, None)
    with lang.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 2
    assert isinstance(resp[0], Modified)
    assert resp[0].filename == "README.md"
    assert resp[0].new_bytes == b"HELLO world\n"
    assert resp[0].diffstat == "+1-1"

    assert isinstance(resp[1], Finished)


@contextmanager
def in_dir(d):
    prev = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(prev)
