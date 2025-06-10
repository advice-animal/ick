import subprocess

from ick.config import RuleConfig
from ick.rules.ast_grep import Rule
from ick_protocol import Finished, Modified


def test_ast_grep_works(tmp_path):
    ast_grep = Rule(
        RuleConfig(
            name="foo",
            impl="ast-grep",
            search="F($$$X)",
            replace="G($$$X)",
        ),
        None,
    )
    ast_grep.prepare()

    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "foo.py").write_text("A(1,2,3)\nF(4,5,6)\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    with ast_grep.work_on_project(tmp_path) as work:
        resp = list(work.run("ast-grep", ["foo.py"]))

    assert len(resp) == 2
    resp[0].diff = "X"
    assert resp[0] == Modified(
        rule_name="ast-grep",
        filename="foo.py",
        new_bytes=b"A(1,2,3)\nG(4,5,6)\n",
        additional_input_filenames=(),
        diffstat="+1-1",
        diff="X",
    )

    assert resp[1] == Finished(
        rule_name="ast-grep",
        error=False,
        message="ast-grep",
    )
