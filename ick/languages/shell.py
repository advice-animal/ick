from __future__ import annotations

import os
import shlex

from ick_protocol import Scope

from ..base_language import BaseHook, ExecWork


class Language(BaseHook):
    work_cls = ExecWork

    def __init__(self, hook_config, repo_config):
        super().__init__(hook_config, repo_config)
        if hook_config.command:
            parts = shlex.split(hook_config.command)
            if hook_config.scope == Scope.SINGLE_FILE:
                self.command_parts = ["xargs", "-n1", "-0"] + parts
            else:
                self.command_parts = parts
        else:
            assert hook_config.data
            self.command_parts = ["/bin/bash", "-c", hook_config.data.strip()]

        # TODO
        self.command_env = os.environ.copy()

    def prepare(self):
        pass
