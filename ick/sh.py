from __future__ import annotations

import os
import subprocess
from logging import getLogger
from pathlib import Path
from typing import Any, Sequence

from keke import ktrace
from vmodule import VLOG_1, VLOG_2

LOG = getLogger(__name__)


@ktrace("cmd", "cwd")
def run_cmd_status(cmd: Sequence[str | Path], check: bool = True, cwd: str | Path | None = None, **kwargs: Any) -> tuple[str, int]:
    cwd = cwd or os.getcwd()
    LOG.log(VLOG_1, "Run %s in %s", cmd, cwd)
    try:
        proc = subprocess.run(cmd, encoding="utf-8", capture_output=True, check=check, cwd=cwd, **kwargs)
    except subprocess.CalledProcessError as e:
        LOG.log(VLOG_2, "Ran %s -> %s", cmd, e.returncode)
        if e.stdout:
            LOG.log(VLOG_2, "Stdout:\n%s", e.stdout)
        if e.stderr:
            LOG.log(VLOG_2, "Stderr:\n%s", e.stderr)
        raise
    LOG.debug("Ran %s -> %s", cmd, proc.returncode)
    LOG.debug("Stdout:\n%s", proc.stdout)
    LOG.debug("Stderr:\n%s", proc.stderr)
    return proc.stdout, proc.returncode


def run_cmd(cmd: Sequence[str | Path], check: bool = True, cwd: str | Path | None = None, **kwargs: Any) -> str:
    output, _ = run_cmd_status(cmd, check, cwd, **kwargs)
    return output
