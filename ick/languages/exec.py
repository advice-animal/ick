"""
A wrapper that supports just "git-diffing" files after running something.
"""

from shlex import split as shlex_split

from ..base_language import BaseHook, ExecWork
from ..config import HookConfig


class Language(BaseHook):
    work_cls = ExecWork

    def __init__(self, conf: HookConfig, repo_config) -> None:
        super().__init__(conf, repo_config)
        self.command_parts = list(shlex_split(conf.command))
        self.command_env = {}
