import os
from pathlib import Path

import appdirs  # type: ignore[import-untyped] # FIX ME

from ick_protocol import Success

from ..base_rule import BaseRule, ExecWork
from ..venv import PythonEnv


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):  # type: ignore[no-untyped-def] # FIX ME
        if not rule_config.replace:
            rule_config.success = Success.NO_OUTPUT
        super().__init__(rule_config, repo_config)  # type: ignore[no-untyped-call] # FIX ME
        venv_key = "ast-grep"
        venv_path = Path(appdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
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

    def prepare(self):  # type: ignore[no-untyped-def] # FIX ME
        self.venv.prepare()  # type: ignore[no-untyped-call] # FIX ME
