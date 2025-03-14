from __future__ import annotations

import subprocess
from contextlib import contextmanager
from logging import getLogger
from typing import Generator, Type

from ick_protocol import Finished, ListResponse, Msg, Scope

from .git_diff import get_diff_messages
from .sh import run_cmd

LOG = getLogger(__name__)


class Work:
    def __init__(self, collection: BaseCollection, project_path):
        self.collection = collection  # BaseHook is a subtype
        self.project_path = project_path

    def invalidate(self, filename):
        pass

    def run(self, hook_name: str, filenames=()):
        """
        Call after `project_path` has settled to execute this collection.

        This should either subprocess `{sys.executable} -m {__name__}`, a
        protocol-speaking tool, or a standard tool and emulate.
        """

        raise NotImplementedError(self.collection.__class__)


class ExecWork(Work):
    def run(self, hook_name, filenames) -> Generator[Msg, None, None]:
        try:
            if self.collection.hook_config.scope == Scope.SINGLE_FILE:
                run_cmd(
                    self.collection.command_parts,
                    env=self.collection.command_env,
                    cwd=self.project_path,
                    input="\0".join(filenames),
                )
            else:
                run_cmd(
                    self.collection.command_parts,
                    env=self.collection.command_env,
                    cwd=self.project_path,
                )
        except FileNotFoundError as e:
            yield Finished(hook_name, error=True, message=str(e))
            return
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                yield Finished(
                    hook_name,
                    error=True,
                    message=(e.stdout or e.stderr or f"{self.collection.command_parts[0]} returned non-zero exit status {e.returncode}"),
                )
            else:
                yield Finished(hook_name, error=True, message=str(e) + "\n" + e.stderr)
            return

        yield from get_diff_messages(hook_name, hook_name, self.project_path)  # TODO msg


class ExecProtocolWork(Work):
    def run(self, hook_name, filenames) -> Generator[Msg, None, None]:
        try:
            if self.collection.hook_config.scope == Scope.SINGLE_FILE:
                run_cmd(self.collection.command_parts + filenames, env=self.collection.command_env, cwd=self.project_path)
            else:
                run_cmd(self.collection.command_parts, env=self.collection.command_env, cwd=self.project_path)
        except FileNotFoundError as e:
            yield Finished(hook_name, error=True, message=str(e))
            return
        except subprocess.CalledProcessError as e:
            yield Finished(hook_name, error=True, message=str(e))
            return

        yield from get_diff_messages(hook_name, hook_name, self.project_path)  # TODO msg
        yield Finished(hook_name)


class BaseCollection:
    work_cls: Type[Work] = Work

    def __init__(self, collection_config, repo_config):
        self.collection_config = collection_config
        self.repo_config = repo_config

    def list(self) -> ListResponse:
        raise NotImplementedError(self.__class__)

    def prepare(self) -> None:
        raise NotImplementedError(self.__class__)

    @contextmanager
    def work_on_project(self, project_path):
        yield self.work_cls(self, project_path)


class BaseHook(BaseCollection):
    def __init__(self, hook_config, repo_config):
        self.hook_config = hook_config
        self.repo_config = repo_config

    def list(self) -> ListResponse:
        return ListResponse(
            hook_names=[self.hook_config.name],
        )
