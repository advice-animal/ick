from __future__ import annotations

import subprocess
from contextlib import contextmanager
from logging import getLogger
from typing import Iterable, Type

from ick_protocol import Finished, ListResponse, Msg, Scope, Success

from .git_diff import get_diff_messages
from .sh import run_cmd

LOG = getLogger(__name__)


class Work:
    def __init__(self, rule: BaseRule, project_path):
        self.rule = rule
        self.project_path = project_path
        self.command_env = {}

    def invalidate(self, filename):
        pass

    def run(self, rule_name: str, filenames=()):
        """
        Call after `project_path` has settled to execute this rule.

        This should either subprocess `{sys.executable} -m {__name__}`, a
        protocol-speaking tool, or a standard tool and emulate.
        """

        raise NotImplementedError(self.rule.__class__)


class ExecWork(Work):
    def run(self, rule_name, filenames) -> Iterable[Msg]:
        try:
            nice_cmd = " ".join(map(str, self.rule.command_parts))
            if self.rule.rule_config.scope == Scope.SINGLE_FILE:
                LOG.info("Running file-scoped command on %s files: %s", len(filenames), nice_cmd)
                stdout = run_cmd(
                    ["xargs", "-P10", "-n10", "-0", *self.rule.command_parts],
                    env=self.rule.command_env,
                    cwd=self.project_path,
                    input="\0".join(filenames),
                )
            else:
                LOG.info("Running project-scoped command in %s: %s", self.project_path, nice_cmd)
                stdout = run_cmd(
                    self.rule.command_parts,
                    env=self.rule.command_env,
                    cwd=self.project_path,
                )
        except FileNotFoundError as e:
            yield Finished(rule_name, error=True, message=str(e))
            return
        except subprocess.CalledProcessError as e:
            yield Finished(
                rule_name,
                error=True,
                message=((e.stdout + e.stderr) or f"{self.rule.command_parts[0]} returned non-zero exit status {e.returncode}"),
            )
            return

        if self.rule.rule_config.success == Success.NO_OUTPUT:
            if stdout:
                yield Finished(
                    rule_name,
                    error=True,
                    message=stdout,
                )
                return

        yield from get_diff_messages(rule_name, rule_name, self.project_path)  # TODO msg


class BaseRule:
    work_cls: Type[Work] = Work

    def __init__(self, rule_config, repo_config):
        self.rule_config = rule_config
        self.repo_config = repo_config
        self.runnable = True
        self.status = ""

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.rule_config.name!r}>"

    def list(self) -> ListResponse:
        return ListResponse(
            rule_names=[self.rule_config.name],
        )

    def prepare(self) -> None:
        raise NotImplementedError(self.__class__)

    @contextmanager
    def work_on_project(self, project_path):
        yield self.work_cls(self, project_path)
