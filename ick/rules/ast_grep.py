import os
from pathlib import Path

import platformdirs

from ick_protocol import Success

from ..base_rule import BaseRule
from ..config import RuleConfig
from ..venv import PythonEnv


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        if not rule_config.replace:
            rule_config.success = Success.NO_OUTPUT
        super().__init__(rule_config)
        venv_key = "ast-grep"
        venv_path = Path(platformdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, ["ast-grep-cli"])
        if rule_config.replace is not None:
            self.command_parts = [
                self.venv.bin("ast-grep"),
                "--pattern",
                rule_config.search,  # type: ignore[list-item] # FIX ME
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
                rule_config.search,  # type: ignore[list-item] # FIX ME
                "--lang",
                "py",
            ]
        # TODO something from here is needed, maybe $HOME, but should be restricted
        self.command_env = os.environ.copy()

    def prepare(self) -> bool:
        return self.venv.prepare()
