import os
from pathlib import Path

import appdirs  # type: ignore[import-untyped] # FIX ME

from ..base_rule import BaseRule, ExecWork
from ..venv import PythonEnv


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config) -> None:  # type: ignore[no-untyped-def] # FIX ME
        super().__init__(rule_config, repo_config)  # type: ignore[no-untyped-call] # FIX ME
        # TODO validate path / rule.name ".py" exists
        venv_key = rule_config.qualname
        venv_path = Path(appdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, self.rule_config.deps)

        self.command_parts = [self.venv.bin("python")]

        if rule_config.data:
            self.command_parts.extend(["-c", rule_config.data])  # type: ignore[list-item] # FIX ME
        else:
            py_script = rule_config.script_path.with_suffix(".py")
            if not py_script.exists():
                self.runnable = False
                self.status = f"Couldn't find implementation {py_script}"
            self.command_parts.extend([py_script])

        self.command_env = os.environ.copy()

    def prepare(self) -> None:
        self.venv.prepare()  # type: ignore[no-untyped-call] # FIX ME
