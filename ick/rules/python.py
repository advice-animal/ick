from __future__ import annotations

import os
import textwrap
from pathlib import Path

import platformdirs

from ..base_rule import BaseRule
from ..config import RuleConfig
from ..venv import PythonEnv


def path_to_module(relative_path: Path) -> str:
    """Convert a file path to a Python module path.

    Args:
        relative_path: Path relative to the repo root (e.g., subdir/script.py)

    Returns:
        Dotted module path (e.g., subdir.script)

    Raises:
        AssertionError: If any path component is not a valid Python identifier
    """
    module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")
    assert all(part.isidentifier() for part in module_path.split(".")), f"Path {relative_path!r} contains invalid Python identifiers"
    return module_path


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        super().__init__(rule_config)

        self.coverage = bool(int(os.environ.get("ICK_COVERAGE_PY", "0")))

        # TODO validate path / rule.name ".py" exists
        assert rule_config.prefixed_name != ""
        venv_key = rule_config.prefixed_name
        venv_path = Path(platformdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        deps = self.rule_config.deps or []
        extra_files: list[tuple[str, str]] = []
        if self.coverage:
            deps += ["coverage"]
            # This config file is written into the rule's venv directory
            # so it won't conflict with other rules running at the same time.
            # The data file is written to the current directory when this rule
            # was instantiated, so the user's working directory.
            assert self.rule_config.script_path is not None
            conf = textwrap.dedent(f"""\
                [run]
                branch = True
                context = $ICK_TEST_NAME
                data_file = {os.getcwd()}/.coverage
                parallel = True
                source = {self.rule_config.script_path.parent}
            """)
            extra_files.append(("coverage.ini", conf))

        self.venv = PythonEnv(venv_path, deps, extra_files)

        self.command_parts = [self.venv.bin("python")]

        if rule_config.data:
            self.command_parts.extend(["-c", textwrap.dedent(rule_config.data)])
            self.coverage = False
        else:
            if self.coverage:
                self.command_parts += ["-m", "coverage", "run", "--rcfile", self.venv.env_path / "coverage.ini"]
            py_script = self.rule_config.script_path.with_suffix(".py")  # type: ignore[union-attr] # FIX ME
            if not py_script.exists():
                self.runnable = False
                self.status = f"Couldn't find implementation {py_script}"

            # Run as a module to support relative imports
            assert rule_config.repo_path is not None
            assert py_script.is_relative_to(rule_config.repo_path)
            relative_path = py_script.relative_to(rule_config.repo_path)
            module_path = path_to_module(relative_path)
            self.command_parts.extend(["-m", module_path])

        self.command_env = os.environ.copy()
        # Add the repo path to PYTHONPATH so rules can import from their own repo
        assert rule_config.repo_path is not None
        pythonpath = self.command_env.get("PYTHONPATH")
        if pythonpath:
            self.command_env["PYTHONPATH"] = f"{rule_config.repo_path}:{pythonpath}"
        else:
            self.command_env["PYTHONPATH"] = str(rule_config.repo_path)
        # Prevent Python from creating __pycache__ bytecode files
        self.command_env["PYTHONDONTWRITEBYTECODE"] = "1"

    def prepare(self) -> bool:
        if not self.venv.prepare():
            return False
        return True
