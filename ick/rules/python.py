from __future__ import annotations

import os
import textwrap
from pathlib import Path

import platformdirs

from ..base_rule import BaseRule
from ..config import RuleConfig
from ..venv import PythonEnv


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        super().__init__(rule_config)

        coverage = bool(int(os.environ.get("ICK_COVERAGE_PY", "0")))

        # TODO validate path / rule.name ".py" exists
        assert rule_config.qualname != ""
        venv_key = rule_config.qualname + ("-cov" if coverage else "")
        venv_path = Path(platformdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        deps = self.rule_config.deps
        if coverage:
            deps = [*(deps or []), "coverage"]
        self.venv = PythonEnv(venv_path, deps)

        self.command_parts = [self.venv.bin("python")]

        if rule_config.data:
            self.command_parts.extend(["-c", textwrap.dedent(rule_config.data)])
        else:
            if coverage:
                coveragerc = venv_path / "coverage.ini"
                Path(coveragerc).write_text(textwrap.dedent(f"""\
                    [run]
                    branch = True
                    data_file = {os.getcwd()}/.coverage
                    parallel = True
                    source = {self.rule_config.script_path.parent}

                    [report]
                    partial_also =
                        if __name__ == .__main__.:

                    """))
                self.command_parts += ["-m", "coverage", "run", "--rcfile", coveragerc]
            py_script = self.rule_config.script_path.with_suffix(".py")  # type: ignore[union-attr] # FIX ME
            if not py_script.exists():
                self.runnable = False
                self.status = f"Couldn't find implementation {py_script}"
            self.command_parts.extend([py_script])

        self.command_env = os.environ.copy()

    def prepare(self) -> bool:
        return self.venv.prepare()
