from pathlib import Path

from helpers import FakeRun

from ick.config import RuleConfig
from ick.rules.docker import Rule
from ick.types_project import BaseRepo, Project


def test_basic_docker(tmp_path: Path) -> None:
    docker_rule = Rule(
        RuleConfig(
            name="append",
            impl="docker",
            scope="repo",  # type: ignore[arg-type] # FIX ME
            command="alpine:3.14 /bin/sh -c 'echo dist >> .gitignore'",
        ),
    )

    run = FakeRun()
    projects = [Project(BaseRepo(Path("/tmp")), "my_subdir/", "shell", "bash.sh")]
    docker_rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1
    assert run.steps[0].cmdline == [
        "docker",
        "run",
        "--rm",
        "-w",
        "/data",
        "-v",
        ".:/data",
        "alpine:3.14",
        "/bin/sh",
        "-c",
        "echo dist >> .gitignore",
    ]
