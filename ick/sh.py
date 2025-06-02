from __future__ import annotations

import os
import subprocess
from logging import getLogger
from pathlib import Path
from typing import Optional, Tuple, Union

from keke import ktrace

LOG = getLogger(__name__)


@ktrace("cmd", "cwd")
def run_cmd(cmd: list[Union[str, Path]], check: bool = True, cwd: Optional[Union[str, Path]] = None, **kwargs) -> Tuple[str, int]:
    cwd = cwd or os.getcwd()
    LOG.info("Run %s in %s", cmd, cwd)
    try:
        proc = subprocess.run(cmd, encoding="utf-8", capture_output=True, check=check, cwd=cwd, **kwargs)
    except subprocess.CalledProcessError as e:
        LOG.info("Ran %s -> %s", cmd, e.returncode)
        if e.stdout:
            LOG.info("Stdout:\n%s", e.stdout)
        if e.stderr:
            LOG.info("Stderr:\n%s", e.stderr)
        raise
    LOG.debug("Ran %s -> %s", cmd, proc.returncode)
    LOG.debug("Stdout:\n%s", proc.stdout)
    LOG.debug("Stderr:\n%s", proc.stderr)
    return proc.stdout, proc.returncode
