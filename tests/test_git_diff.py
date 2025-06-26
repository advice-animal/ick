import os
import subprocess
from pathlib import Path

from ick.git_diff import get_diff_messages
from ick_protocol import Finished, Modified


def test_smoketest(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    Path("foo.txt").write_text("line\n")
    messages = list(get_diff_messages("m", "foo", Path.cwd()))
    assert len(messages) == 2
    assert isinstance(messages[0], Modified)
    assert messages[0].diffstat == "+1-0"
    assert messages[0].new_bytes == b"line\n"

    assert isinstance(messages[1], Finished)


def test_smoketest_workdir(tmp_path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    Path(tmp_path, "foo.txt").write_text("line\n")
    messages = list(get_diff_messages("m", "foo", tmp_path))
    assert len(messages) == 2
    assert isinstance(messages[0], Modified)
    assert messages[0].diffstat == "+1-0"
    assert messages[0].new_bytes == b"line\n"

    assert isinstance(messages[1], Finished)


def test_smoketest_removal(tmp_path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    Path(tmp_path, "foo.txt").write_text("line\nunchanged\n")
    subprocess.check_call(["git", "add", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "sync"], cwd=tmp_path)
    Path(tmp_path, "foo.txt").write_text("other\nunchanged\n")
    messages = list(get_diff_messages("m", "foo", tmp_path))
    assert len(messages) == 2
    assert isinstance(messages[0], Modified)
    assert messages[0].diffstat == "+1-1"
    assert messages[0].new_bytes == b"other\nunchanged\n"

    assert isinstance(messages[1], Finished)


def test_smoketest_binary(tmp_path: Path) -> None:
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    Path("foo.bin").write_bytes(b"\x00\x01\x02")
    subprocess.check_call(["git", "add", "."])
    messages = list(get_diff_messages("m", "foo", Path.cwd()))
    assert len(messages) == 2
    assert isinstance(messages[0], Modified)
    assert messages[0].diffstat == "+0-0"  # confusing
    assert messages[0].new_bytes == b"\x00\x01\x02"

    assert isinstance(messages[1], Finished)
