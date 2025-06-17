import subprocess
import sys

import pytest

from ick.config import RuleConfig
from ick.rules.docker import Rule
from ick_protocol import Finished, Modified


@pytest.mark.skipif(sys.platform == "darwin", reason="GHA can't test docker")
def test_basic_docker(tmp_path):
    docker_rule = Rule(
        RuleConfig(
            name="append",
            impl="docker",
            scope="repo",
            command="alpine:3.14 /bin/sh -c 'echo dist >> .gitignore'",
        ),
        None,
    )
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    subprocess.check_call(["git", "add", ".gitignore"], cwd=tmp_path)
    subprocess.check_call(["git", "commit", "-a", "-msync"], cwd=tmp_path)

    docker_rule.prepare()
    with docker_rule.work_on_project(tmp_path) as work:
        resp = list(work.run("foo", [".gitignore"]))

    assert len(resp) == 2
    resp[0].diff = "X"
    assert resp[0] == Modified(
        rule_name="foo",
        filename=".gitignore",
        new_bytes=b"*.pyc\ndist\n",
        additional_input_filenames=(),
        diffstat="+1-0",
        diff="X",
    )

    assert resp[1] == Finished(
        rule_name="foo",
        error=False,
        message="foo",
    )
