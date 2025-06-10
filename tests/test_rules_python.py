import subprocess

from ick.config import RuleConfig
from ick.rules.python import Rule
from ick_protocol import Finished, Modified


def test_python_works(tmp_path):
    pyrule = Rule(
        RuleConfig(
            name="foo",
            impl="python",
            inputs=["*.py"],
            data="""\
import sys
import attrs
for f in sys.argv[1:]:
    with open(f, "w") as fo:
        fo.write("new\\n")
""",
            deps=["attrs"],
        ),
        None,
    )
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "foo.py").write_text("xhello\n")
    (tmp_path / "foo.txt").write_text("xhello\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    pyrule.prepare()

    with pyrule.work_on_project(tmp_path) as work:
        resp = list(work.run("foo", ["foo.py"]))

    assert len(resp) == 2
    resp[0].diff = "X"
    assert resp[0] == Modified(
        rule_name="foo",
        filename="foo.py",
        new_bytes=b"new\n",
        additional_input_filenames=(),
        diffstat="+1-1",
        diff="X",
    )

    assert resp[1] == Finished(
        rule_name="foo",
        error=False,
        message="foo",
    )
