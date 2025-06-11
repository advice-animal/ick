import subprocess

from ick.config import RuleConfig
from ick.rules.shell import Rule
from ick_protocol import Finished, Modified


def test_smoke_single_file(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = RuleConfig(
        name="hello",
        impl="shell",
        command="sed -i -e 's/hello/HELLO/'",
    )
    rule = Rule(conf, None)
    with rule.work_on_project(tmp_path) as work:
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

    conf = RuleConfig(
        name="hello",
        impl="shell",
        command="/bin/zzyzx",
    )
    rule = Rule(conf, None)
    with rule.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 1
    assert isinstance(resp[0], Finished)
    assert resp[0].error
    assert "xargs: /bin/zzyzx: No such file or directory" in resp[0].message


def test_smoke_failure(tmp_path):
    # This duplicates stuff that ick.runner does
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("hello world\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-m", "temp"], cwd=tmp_path)

    conf = RuleConfig(
        name="hello",
        impl="shell",
        command="/bin/sh -c 'exit 1'",
    )
    rule = Rule(conf, None)
    with rule.work_on_project(tmp_path) as work:
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

    conf = RuleConfig(
        name="hello",
        impl="shell",
        scope="repo",
        command="sed -i -e 's/hello/HELLO/' README.md",
    )
    rule = Rule(conf, None)
    with rule.work_on_project(tmp_path) as work:
        resp = list(work.run("hello", ["README.md"]))

    assert len(resp) == 2
    assert isinstance(resp[0], Modified)
    assert resp[0].filename == "README.md"
    assert resp[0].new_bytes == b"HELLO world\n"
    assert resp[0].diffstat == "+1-1"

    assert isinstance(resp[1], Finished)
