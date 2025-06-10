import subprocess

from ick.config import RuleConfig
from ick.rules.merge_toml import Rule
from ick_protocol import Finished, Modified


def test_merge_toml_works(tmp_path):
    merge_toml = Rule(
        RuleConfig(
            name="foo",
            impl="merge_toml",
            data="""\
[foo]
baz = 99
""",
        ),
        None,
    )
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / "foo.toml").write_text("# doc comment\n[foo]\nbar = 0\nbaz = 1\nfloof = 2\n")
    subprocess.check_call(["git", "add", "-N", "."], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    with merge_toml.work_on_project(tmp_path) as work:
        resp = list(work.run("merge_toml", ["foo.toml"]))

    assert len(resp) == 2
    resp[0].diff = "X"
    assert resp[0] == Modified(
        rule_name="merge_toml",
        filename="foo.toml",
        new_bytes=b"# doc comment\n[foo]\nbar = 0\nbaz = 99\nfloof = 2\n",
        additional_input_filenames=(),
        diffstat="+1-1",
        diff="X",
    )

    assert resp[1] == Finished(
        rule_name="merge_toml",
        error=False,
        message="merge_toml",
    )
