from __future__ import annotations

import subprocess
from contextlib import contextmanager
from typing import Generator, Type

from ick_protocol import Finished, ListResponse, Msg, Scope

from .git_diff import get_diff_messages


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

        raise NotImplementedError()


class ExecWork(Work):
    def run(self, hook_name, filenames) -> Generator[Msg, None, None]:
        try:
            if self.collection.hook_config.scope == Scope.SINGLE_FILE:
                subprocess.check_call(self.collection.command_parts + filenames, env=self.collection.command_env, cwd=self.project_path)
            else:
                subprocess.check_call(self.collection.command_parts, env=self.collection.command_env, cwd=self.project_path)
        except FileNotFoundError as e:
            yield Finished(hook_name, error=True, message=str(e))
            return
        except subprocess.CalledProcessError as e:
            yield Finished(hook_name, error=True, message=str(e))
            return

        yield from get_diff_messages(hook_name, hook_name, self.project_path)  # TODO msg


class ExecProtocolWork(Work):
    def run(self, hook_name, filenames) -> Generator[Msg, None, None]:
        try:
            if self.collection.hook_config.scope == Scope.SINGLE_FILE:
                subprocess.check_call(self.collection.command_parts + filenames, env=self.collection.command_env, cwd=self.project_path)
            else:
                subprocess.check_call(self.collection.command_parts, env=self.collection.command_env, cwd=self.project_path)
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
        raise NotImplementedError()

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
