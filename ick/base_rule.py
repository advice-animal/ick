from __future__ import annotations

import os
import subprocess
from fnmatch import fnmatch
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Optional, Sequence

import moreorless
from feedforward import Notification, Run, State, Step
from feedforward.erasure import ERASURE
from keke import ktrace

from ick_protocol import Finished, ListResponse, Modified, Scope

from .config import RuleConfig
from .sh import run_cmd

LOG = getLogger(__name__)


def materialize(path: str, filename: str, contents: bytes):
    Path(path, filename).parent.mkdir(exist_ok=True, parents=True)
    Path(path, filename).write_bytes(contents)


class GenericPreparedStep(Step):
    def __init__(
        self,
        qualname: str,
        patterns: Sequence[str],
        project_path: str,
        cmdline,
        extra_env: dict[str, str],
        append_filenames: bool,
        rule_prepare=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.qualname = qualname
        # TODO figure out how extra_inputs factors in
        assert patterns is not None
        self.patterns = patterns
        self.match_prefix = project_path
        self.cmdline = cmdline
        self.extra_env = extra_env
        self.append_filenames = append_filenames
        self.rule_prepare = rule_prepare
        self.messages = []
        self.rule_status = True  # Success

    def match(self, key):
        return match_prefix_patterns(key, self.match_prefix, self.patterns)

    def run_next_batch(self):
        # TODO document that we expect rule_prepare to handle a thundering herd (probably by returning False)
        if self.unprocessed_notifications and self.rule_prepare and not self.rule_prepare():
            return False

        return super().run_next_batch()

    _g_files = {}

    def _gravitational_constant(self):
        return 1

    @ktrace("self.qualname", "self.project_path", "next_gen")
    def process(self, next_gen: int, notifications):
        notifications = list(notifications)
        # TODO name better, pick a good one...
        with TemporaryDirectory() as d:
            # with self.state_lock:
            #     # First the common files
            #     g = self._gravitational_constant()
            #     for k, v in self._g_files.items():
            #         materialize(d, k, v)

            # Then the ones we're being asked to do
            filenames = []
            for n in notifications:
                if n.state.value is ERASURE:
                    continue
                relative_filename = n.key[len(self.match_prefix) :]
                materialize(d, relative_filename, n.state.value)
                filenames.append(relative_filename)

            # nice_cmd = " ".join(map(str, self.cmdline))
            if self.append_filenames:
                cmd = self.cmdline + filenames
            else:
                cmd = self.cmdline

            env = os.environ.copy()
            env.update(self.extra_env)

            try:
                run_cmd(
                    cmd,
                    env=env,
                    cwd=d,
                )
            except FileNotFoundError as e:
                self.cancel(str(e))
                return
            except subprocess.CalledProcessError as e:
                if e.stdout:
                    self.messages.append(e.stdout)
                if e.stderr:
                    self.messages.append(e.stderr)

                if e.returncode == 99:
                    self.rule_status = False
                else:
                    self.rule_status = None

            expected = {n.key[len(self.match_prefix) :]: n.state.value for n in notifications if n.state.value is not ERASURE}
            changed, new, remv = analyze_dir(d, expected)
            # print(changed, new, remv)

            for n in notifications:
                relative_filename = n.key[len(self.match_prefix) :]
                if relative_filename in changed:
                    yield self.update_notification(n, next_gen, new_value=Path(d, relative_filename).read_bytes())
                elif relative_filename in remv:
                    yield self.update_notification(n, next_gen, new_value=ERASURE)

            brand_new_gens = self.update_generations((0,) * len(notifications[0].state.gens), next_gen)
            for name in new:
                yield Notification(
                    key=name,
                    state=State(
                        gens=brand_new_gens,
                        value=Path(d, name).read_bytes(),
                    ),
                )

    def compute_diff_messages(self):
        assert not self.cancelled
        assert self.outputs_final

        changes = []
        for k in set(self.accepted_state) | set(self.output_state):
            if k in self.accepted_state and k in self.output_state:
                # Diff but be careful of erasures...
                a = self.accepted_state[k].value
                b = self.output_state[k].value
                if a == b:
                    continue
                elif isinstance(a, bytes) and isinstance(b, bytes):
                    # TODO non-utf8 files
                    diff = moreorless.unified_diff(a.decode(), b.decode(), k)
                elif a is ERASURE:
                    # Should really say /dev/null input
                    diff = moreorless.unified_diff("", b.decode(), k)
                else:
                    # Should really say /dev/null input
                    diff = moreorless.unified_diff(a.decode(), "", k)

                diffstat = "+%d-%d" % (diff.count("\n+"), diff.count("\n-"))

                changes.append(
                    Modified(rule_name=self.qualname, filename=k, new_bytes=None if b is ERASURE else b, diff=diff, diffstat=diffstat)
                )
            elif k not in self.accepted_state:
                # Well then...
                changes.append(Modified(rule_name=self.qualname, filename=k, new_bytes=self.output_state[k].value))

        changes.append(
            Finished(self.qualname, status=self.rule_status, message="".join(self.messages)),
        )
        return changes


def analyze_dir(directory, expected: dict[str, bytes]):
    # TODO dicts?
    changed = set()
    new = set()
    unchanged = set()
    for name, dirnames, filenames in os.walk(directory):
        for f in filenames:
            relative = Path(name, f).relative_to(directory).as_posix()
            data = Path(name, f).read_bytes()
            expected_data = expected.get(relative)
            if expected_data is None:
                new.add(relative)
            elif expected_data != data:
                changed.add(relative)
            else:
                unchanged.add(relative)

    remv = set(expected) - changed - unchanged

    return changed, new, remv


def match_prefix_patterns(filename, prefix, patterns) -> Optional[str]:
    """
    Returns the prefix-removed filename if it matches, otherwise None.
    """
    if filename.startswith(prefix):
        filename = filename[len(prefix) :].lstrip("/")
        if any(fnmatch(filename, pat) for pat in patterns):
            return filename
    return None


class BaseRule:
    def __init__(self, rule_config: RuleConfig) -> None:
        self.rule_config = rule_config
        self.runnable = True
        self.status = ""
        self.command_parts: Sequence[str | Path] = []
        self.command_env: Mapping[str, str | bytes] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.rule_config.name!r}>"

    def list(self) -> ListResponse:
        return ListResponse(
            rule_names=[self.rule_config.name],
        )

    def prepare(self) -> bool:
        return True  # no setup required

    def add_steps_to_run(self, projects: Any, run: Run) -> None:
        qualname = self.rule_config.qualname

        if self.rule_config.scope == Scope.FILE:
            for p in projects:
                run.add_step(
                    GenericPreparedStep(
                        qualname=qualname,
                        patterns=self.rule_config.inputs,
                        project_path=p.subdir,
                        cmdline=self.command_parts,
                        extra_env=self.command_env,
                        append_filenames=True,
                        rule_prepare=self.prepare,
                    )
                )
        else:
            run.add_step(
                GenericPreparedStep(
                    qualname=qualname,
                    patterns=self.rule_config.inputs or ("*",),
                    project_path="",
                    cmdline=self.command_parts,
                    extra_env=self.command_env,
                    append_filenames=False,
                    rule_prepare=self.prepare,
                    eager=False,
                )
            )
            # run.add_step(GenericPreparedStep(
            #     patterns = self.rule.rule_config.inputs,
            #     project=None,
            #     cmdline=self.command_parts,
            #     extra_env=self.command_env,
            #     append_filenames=False,
            # ))
