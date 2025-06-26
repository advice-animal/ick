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
    def __init__(self, rule: BaseRule, project_path):  # type: ignore[no-untyped-def] # FIX ME
        self.rule = rule
        self.project_path = project_path
        self.command_env = {}  # type: ignore[var-annotated] # FIX ME

    def invalidate(self, filename):  # type: ignore[no-untyped-def] # FIX ME
        pass

    def run(self, rule_name: str, filenames=()):  # type: ignore[no-untyped-def] # FIX ME
        """
        Call after `project_path` has settled to execute this rule.

        This should either subprocess `{sys.executable} -m {__name__}`, a
        protocol-speaking tool, or a standard tool and emulate.
        """

        raise NotImplementedError(self.rule.__class__)


class ExecWork(Work):
    def run(self, rule_name, filenames) -> Iterable[Msg]:  # type: ignore[no-untyped-def, override] # FIX ME
        try:
            nice_cmd = " ".join(map(str, self.rule.command_parts))  # type: ignore[attr-defined] # FIX ME
            if self.rule.rule_config.scope == Scope.FILE:
                if not filenames:
                    LOG.info("Skipping run because there are no files matched: %s", nice_cmd)
                    yield Finished(
                        rule_name,
                        error=False,
                        message="",
                    )
                    return
                LOG.info("Running file-scoped command on %s files: %s", len(filenames), nice_cmd)
                stdout = run_cmd(
                    ["xargs", "-P10", "-n10", "-0", *self.rule.command_parts],  # type: ignore[attr-defined] # FIX ME
                    env=self.rule.command_env,  # type: ignore[attr-defined] # FIX ME
                    cwd=self.project_path,
                    input="\0".join(filenames),
                )
            else:
                LOG.info("Running project-scoped command in %s: %s", self.project_path, nice_cmd)
                stdout = run_cmd(
                    self.rule.command_parts,  # type: ignore[attr-defined] # FIX ME
                    env=self.rule.command_env,  # type: ignore[attr-defined] # FIX ME
                    cwd=self.project_path,
                )
        except FileNotFoundError as e:
            yield Finished(rule_name, error=True, message=str(e))
            return
        except subprocess.CalledProcessError as e:
            yield Finished(
                rule_name,
                error=True,
                message=((e.stdout + e.stderr) or f"{self.rule.command_parts[0]} returned non-zero exit status {e.returncode}"),  # type: ignore[attr-defined] # FIX ME
            )
            return

        if self.rule.rule_config.success == Success.NO_OUTPUT:
            if stdout:
                yield Finished(
                    rule_name,
                    error=True,
                    message=stdout,  # type: ignore[arg-type] # FIX ME
                )
                return

        yield from get_diff_messages(rule_name, rule_name, self.project_path)  # TODO msg


class BaseRule:
    work_cls: Type[Work] = Work

    def __init__(self, rule_config, repo_config):  # type: ignore[no-untyped-def] # FIX ME
        self.rule_config = rule_config
        self.repo_config = repo_config
        self.runnable = True
        self.status = ""

    def __repr__(self):  # type: ignore[no-untyped-def] # FIX ME
        return f"<{self.__class__.__name__} name={self.rule_config.name!r}>"

    def list(self) -> ListResponse:
        return ListResponse(
            rule_names=[self.rule_config.name],
        )

    def prepare(self) -> None:
        raise NotImplementedError(self.__class__)

    @contextmanager
    def work_on_project(self, project_path):  # type: ignore[no-untyped-def] # FIX ME
        yield self.work_cls(self, project_path)
