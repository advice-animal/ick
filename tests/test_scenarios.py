from __future__ import annotations

import dataclasses
import os
import re
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Iterable

import pytest
from click.testing import CliRunner

from ick.cmdline import main

SCENARIO_DIR = Path(__file__).parent / "scenarios"
SCENARIOS = sorted(str(f.relative_to(SCENARIO_DIR)) for f in SCENARIO_DIR.glob("*/*.txt"))

LOG_LINE_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} ", re.M)
LOG_LINE_NUMERIC_LINE_RE = re.compile(r"^([A-Z]+\s+[a-z_.]+:)\d+(?= )", re.M)
GIT_VERSION_RE = re.compile(r"(\d+\.)\d+(?:\.\d+)?(?:\.dev\d+\S+)?")
TRAILING_WHITESPACE = re.compile(r"(?m) +$")


def clean_output(output: str) -> str:
    cleaned_output = LOG_LINE_TIMESTAMP_RE.sub("", output)
    cleaned_output = LOG_LINE_NUMERIC_LINE_RE.sub(lambda m: (m.group(1) + "<n>"), cleaned_output)
    cleaned_output = GIT_VERSION_RE.sub(lambda m: (m.group(1) + "<stuff>"), cleaned_output)
    cleaned_output = TRAILING_WHITESPACE.sub("", cleaned_output)
    cleaned_output = cleaned_output.replace(os.getcwd(), "/CWD")
    return cleaned_output


@pytest.mark.parametrize("filename", SCENARIOS)
def test_scenario(filename, monkeypatch) -> None:  # type: ignore[no-untyped-def] # FIX ME
    __tracebackhide__ = True
    # Avoid reading user-level config in tests, as they probably would change
    # the available rules
    monkeypatch.setenv("XDG_CONFIG_HOME", "/")

    path = SCENARIO_DIR / filename
    commands = load_scenario(path)
    update = bool(int(os.getenv("UPDATE_SCENARIOS", "0")))

    cli_runner = CliRunner()
    with cli_runner.isolated_filesystem():
        repo_data = path.parent / "repo"
        Path(".gitconfig").write_text(
            textwrap.dedent("""
                [user]
                name = Tests
                email = test@example.com
                [init]
                defaultBranch = main    # just to quiet the hints
                """)
        )
        monkeypatch.setenv("HOME", os.getcwd())
        if repo_data.exists():
            shutil.copytree(repo_data, ".", dirs_exist_ok=True)
            # TODO the commit here is necessary; project finding only works based
            # on files that are present in the original repo, and this doesn't work
            # with NullRepo either. Oops.
            subprocess.check_call(["git", "init"])
            subprocess.check_call(["git", "add", "-N", "."])
            subprocess.check_call(["git", "commit", "-a", "-m", "foo"])
        for command in commands:
            if command.command[:6] == "$ ick ":
                # TODO: handle global options like -vv
                args = shlex.split(command.command[6:])
                with monkeypatch.context() as m:
                    m.setenv("COLUMNS", "999")
                    m.setattr(
                        "ick.runner.Runner._testing_replacements",
                        {
                            os.getcwd(): "/CWD",
                        },
                    )
                    result = cli_runner.invoke(main, args, catch_exceptions=False)
                output = result.output
                if result.exit_code != 0:
                    output += f"(exit status: {result.exit_code})\n"
            elif command.command == "":
                # This happens with trailing comment lines in the scenario, so
                # there's no command or output.
                output = ""
            else:
                assert command.command[:2] == "$ "
                # We use shell=True so that scenarios can use shell features
                # like redirection, pipes, sub-commands, and so on.
                proc = subprocess.run(
                    command.command[2:],
                    encoding="utf-8",
                    shell=True,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                output = proc.stdout
                if proc.returncode != 0:
                    output += f"(exit status: {proc.returncode})\n"

            cleaned_output = clean_output(output)
            if update:
                command.output = cleaned_output  # pragma: nocover
            else:
                assert cleaned_output == command.output

    if update:  # pragma: nocover
        save_scenario(path, commands)


@dataclasses.dataclass
class ScenarioCommand:
    comments: str = ""
    command: str = ""
    output: str = ""


def load_scenario(path: Path) -> Iterable[ScenarioCommand]:
    with open(path) as f:
        return parse_scenario(f)


def parse_scenario(lines: Iterable[str]) -> Iterable[ScenarioCommand]:
    commands: list[ScenarioCommand] = []
    command: ScenarioCommand = ScenarioCommand()
    found_command = False

    def new_command() -> None:
        nonlocal command, found_command
        if command is not None:
            commands.append(command)
        command = ScenarioCommand()
        found_command = False

    for line in lines:
        if line.startswith("#") or (line.strip() == "" and not found_command):
            if found_command:
                new_command()
            command.comments += line
        elif line.startswith("$"):
            if found_command:
                new_command()
            command.command = line
            found_command = True
        else:
            command.output += line

    new_command()
    return commands


@pytest.mark.parametrize(
    "text, commands",
    [
        # These tests only parse the scenarios, not run them, so the scenario
        # data here doesn't show actual execution.
        (
            """
            # a comment

            $ echo hello
            hello
            """,
            [ScenarioCommand("# a comment\n\n", "$ echo hello\n", "hello\n")],
        ),
        (
            """
            $ echo hello
            hello
            # Another command coming

            # Look:
            $ do_nothing
            $ cat the_file.txt
            line 1

            line 3
            # All done.
            """,
            [
                ScenarioCommand("", "$ echo hello\n", "hello\n"),
                ScenarioCommand("# Another command coming\n\n# Look:\n", "$ do_nothing\n", ""),
                ScenarioCommand("", "$ cat the_file.txt\n", "line 1\n\nline 3\n"),
                ScenarioCommand("# All done.\n", "", ""),
            ],
        ),
    ],
)
def test_parse_scenario(text, commands) -> None:  # type: ignore[no-untyped-def] # FIX ME
    lines = textwrap.dedent(text[1:]).splitlines(keepends=True)
    assert list(parse_scenario(lines)) == commands


def save_scenario(path: Path, commands: Iterable[ScenarioCommand]) -> None:  # pragma: nocover
    lines = []
    for command in commands:
        lines.append(command.comments)
        lines.append(command.command)
        lines.append(command.output)

    path.write_text("".join(lines))
