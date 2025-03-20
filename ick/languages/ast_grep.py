import os
from pathlib import Path

import appdirs

from ..base_language import BaseRule, ExecWork
from ..venv import PythonEnv


class Language(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        venv_key = "ast-grep"
        venv_path = Path(appdirs.user_cache_dir("advice-animal", "ick"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, ["ast-grep-cli"])
        if rule_config.replace is not None:
            self.command_parts = [
                self.venv.bin("ast-grep"),
                "--pattern",
                rule_config.search,
                "--rewrite",
                rule_config.replace,
                "--lang",
                "py",
                "-U",
            ]
        else:
            # TODO output rule_config.message if found
            self.command_parts = [
                self.venv.bin("ast-grep"),
                "--pattern",
                rule_config.search,
                "--lang",
                "py",
            ]
        # TODO something from here is needed, maybe $HOME, but should be restricted
        self.command_env = os.environ.copy()

    def prepare(self):
        self.venv.prepare()
