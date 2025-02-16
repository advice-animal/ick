import subprocess

from ick.config import HookConfig
from ick.languages.pygrep import Language


def test_pygrep_works(tmp_path):
    pygrep = Language(
        HookConfig(
            name="foo",
            language="pygrep",
            search="hello",
            replace="bar",
        ),
        None,
    )
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "foo.py").write_text("hello\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    with pygrep.work_on_project(tmp_path) as work:
        resp = list(work.run("pygrep", ["foo.py"]))

    assert len(resp) == 2
