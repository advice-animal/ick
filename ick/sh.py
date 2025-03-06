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
    proc = subprocess.run(cmd, encoding="utf-8", capture_output=True, check=check, cwd=cwd, **kwargs)
    LOG.debug("Ran %s -> %s", cmd, proc.returncode)
    LOG.debug("Stdout: %s", proc.stdout)
    return proc.stdout, proc.returncode
