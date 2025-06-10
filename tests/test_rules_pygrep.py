import subprocess

from ick.config import RuleConfig
from ick.rules.pygrep import Rule
from ick_protocol import Finished, Modified


def test_pygrep_works(tmp_path):
    pygrep = Rule(
        RuleConfig(
            name="foo",
            impl="pygrep",
            search="hello",
            replace="bar",
        ),
        None,
    )
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "foo.py").write_text("xhello\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    with pygrep.work_on_project(tmp_path) as work:
        resp = list(work.run("pygrep", ["foo.py"]))

    assert len(resp) == 2
    resp[0].diff = "X"
    assert resp[0] == Modified(
        rule_name="pygrep",
        filename="foo.py",
        new_bytes=b"xbar\n",
        additional_input_filenames=(),
        diffstat="+1-1",
        diff="X",
    )

    assert resp[1] == Finished(
        rule_name="pygrep",
        error=False,
        message="pygrep",
    )
