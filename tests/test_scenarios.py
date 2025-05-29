from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Optional, Tuple

import pytest
from click.testing import CliRunner

from ick.cmdline import main

SCENARIO_DIR = Path(__file__).parent / "scenarios"
SCENARIOS = sorted(SCENARIO_DIR.glob("*.txt"))

LOG_LINE_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} ", re.M)
LOG_LINE_NUMERIC_LINE_RE = re.compile(r"^([A-Z]+\s+[a-z_.]+:)\d+(?= )", re.M)
GIT_VERSION_RE = re.compile(r"(\d+\.)\d+(?:\.\d+)?(?:\.dev\d+\S+)?")


@pytest.mark.parametrize("filename", SCENARIOS)
def test_scenario(filename, monkeypatch):
    monkeypatch.setenv("ADVICE_DIR", str(Path(__file__).parent / "advice"))

    path = SCENARIO_DIR / filename
    runner = CliRunner()
    command, output = load_scenario(path)

    with runner.isolated_filesystem():
        result = runner.invoke(main, command, catch_exceptions=False)

    cleaned_output = LOG_LINE_TIMESTAMP_RE.sub("", result.output)
    cleaned_output = LOG_LINE_NUMERIC_LINE_RE.sub(lambda m: (m.group(1) + "<n>"), cleaned_output)
    cleaned_output = GIT_VERSION_RE.sub(lambda m: (m.group(1) + "<stuff>"), cleaned_output)

    if os.getenv("UPDATE_SCENARIOS"):
        save_scenario(path, cleaned_output)
    else:
        assert output == cleaned_output


def load_scenario(path: Path) -> Tuple[Tuple[str, ...], str]:
    command: Optional[Tuple[str, ...]] = None
    output: str = ""
    state = 0
    with open(path) as f:
        for line in f:
            if state == 0 and line.startswith("#"):
                pass
            elif state == 0 and line.startswith("$"):
                parts = shlex.split(line[1:])
                assert parts[0] == "ick"
                command = tuple(parts[1:])
                state = 1
            elif state == 1:
                output += line

    assert state == 1
    assert command is not None
    return (command, output)


def save_scenario(path: Path, new_output: str) -> None:
    state = 0
    buf = ""
    with open(path) as f:
        for line in f:
            if state == 0 and line.startswith("#"):
                buf += line
            elif state == 0 and line.startswith("$"):
                buf += line
                state = 1

    assert state == 1
    if not buf.endswith("\n"):
        buf += "\n"
    path.write_text(buf + new_output)
