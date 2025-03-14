import os
from pathlib import Path

import appdirs

from ..base_language import BaseHook, ExecWork
from ..venv import PythonEnv


class Language(BaseHook):
    work_cls = ExecWork

    def __init__(self, hook_config, repo_config):
        super().__init__(hook_config, repo_config)
        venv_key = "ast-grep"
        venv_path = Path(appdirs.user_cache_dir("advice-animal", "ick"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, ["ast-grep-cli"])
        if hook_config.replace is not None:
            self.command_parts = [
                self.venv.bin("ast-grep"),
                "--pattern",
                hook_config.search,
                "--rewrite",
                hook_config.replace,
                "--lang",
                "py",
                "-U",
            ]
        else:
            # TODO output hook_config.message if found
            self.command_parts = [
                self.venv.bin("ast-grep"),
                "--pattern",
                hook_config.search,
                "--lang",
                "py",
            ]
        # TODO something from here is needed, maybe $HOME, but should be restricted
        self.command_env = os.environ.copy()

    def prepare(self):
        self.venv.prepare()
