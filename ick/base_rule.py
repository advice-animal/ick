from __future__ import annotations

import os
import subprocess
from fnmatch import fnmatch
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable, Mapping, Sequence

import moreorless
from feedforward import Notification, Run, State, Step
from feedforward.erasure import ERASURE, Erasure
from keke import ktrace

from ick_protocol import Finished, ListResponse, Modified, RuleStatus, Scope

from .config import RuleConfig
from .sh import run_cmd
from .util import diffstat

LOG = getLogger(__name__)


def materialize(path: str, filename: str, contents: bytes) -> None:
    Path(path, filename).parent.mkdir(exist_ok=True, parents=True)
    Path(path, filename).write_bytes(contents)


class GenericPreparedStep(Step[str, bytes | Erasure]):
    def __init__(
        self,
        qualname: str,
        patterns: Sequence[str],
        project_path: str,
        cmdline: Sequence[str | Path],
        extra_env: dict[str, str],
        append_filenames: bool,
        rule_prepare: Callable[[], bool] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.qualname = qualname
        # TODO figure out how extra_inputs factors in
        assert patterns is not None, "File scoped rules require an `inputs` section in the rule config!"
        self.patterns = patterns
        self.match_prefix = project_path
        self.cmdline = cmdline
        self.extra_env = extra_env
        self.append_filenames = append_filenames
        self.rule_prepare = rule_prepare
        # dict key is gen, (keys, ...) and for these to match precisely we
        # should have output_state gens[self.index] == gen for all the listed
        # keys; if we have none of them then we should skip that message.
        #
        # dict value is output, exit code and we decide what the aggregate code
        # is at the end.
        self.batch_messages: dict[tuple[tuple[str, int], ...], tuple[str, int]] = {}
        self.rule_status = RuleStatus.SUCCESS

    def match(self, key: str) -> bool:
        return match_prefix_patterns(key, self.match_prefix, self.patterns) is not None

    def run_next_batch(self) -> bool:
        # TODO document that we expect rule_prepare to handle a thundering herd (probably by returning False)
        if self.unprocessed_notifications and self.rule_prepare and not self.rule_prepare():
            return False

        return super().run_next_batch()

    _g_files: dict[str, bytes] = {}

    def _gravitational_constant(self) -> int:
        return 1

    @ktrace("self.qualname", "self.match_prefix", "next_gen")
    def process(
        self,
        next_gen: int,
        notifications: Iterable[Notification[str, bytes | Erasure]],
    ) -> Iterable[Notification[str, bytes | Erasure]]:
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
            batch_key = {}
            batch_value = None
            for n in notifications:
                if n.state.value is ERASURE:
                    continue
                relative_filename = n.key[len(self.match_prefix) :]
                materialize(d, relative_filename, n.state.value)
                filenames.append(relative_filename)
                assert self.index is not None
                batch_key[n.key] = n.state.gens[self.index]

            # nice_cmd = " ".join(map(str, self.cmdline))
            if self.append_filenames:
                cmd = list(self.cmdline) + filenames
            else:
                cmd = list(self.cmdline)

            env = os.environ.copy()
            env.update(self.extra_env)

            try:
                stdout = run_cmd(
                    cmd,
                    env=env,
                    cwd=d,
                )
            except FileNotFoundError as e:
                self.cancel(str(e))
                return
            except subprocess.CalledProcessError as e:
                msg = ""
                if e.stdout:
                    msg += e.stdout
                if e.stderr:
                    msg += e.stderr

                batch_value = (msg, e.returncode)
            else:
                batch_value = (stdout, 0)

            expected = {n.key[len(self.match_prefix) :]: n.state.value for n in notifications if n.state.value is not ERASURE}
            changed, new, remv = analyze_dir(d, expected)
            # print(changed, new, remv)

            for n in notifications:
                relative_filename = n.key[len(self.match_prefix) :]
                if relative_filename in changed:
                    yield self.update_notification(n, next_gen, new_value=Path(d, relative_filename).read_bytes())
                    batch_key[n.key] = next_gen
                elif relative_filename in remv:
                    yield self.update_notification(n, next_gen, new_value=ERASURE)
                    batch_key[n.key] = next_gen

            brand_new_gens = self.update_generations((0,) * len(notifications[0].state.gens), next_gen)
            for name in new:
                batch_key[name] = next_gen
                yield Notification(
                    key=name,
                    state=State(
                        gens=brand_new_gens,
                        value=Path(d, name).read_bytes(),
                    ),
                )
            if batch_value:
                self.batch_messages[tuple(batch_key.items())] = batch_value

    def compute_diff_messages(self) -> list[Modified | Finished]:
        assert not self.cancelled
        assert self.outputs_final
        assert self.index is not None

        changes: list[Modified | Finished] = []
        for k in sorted(set(self.accepted_state) | set(self.output_state)):
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
                    assert isinstance(b, bytes)
                    diff = moreorless.unified_diff("", b.decode(), k)
                else:
                    # Should really say /dev/null input
                    diff = moreorless.unified_diff(a.decode(), "", k)

                changes.append(
                    Modified(
                        rule_name=self.qualname,
                        filename=k,
                        new_bytes=None if b is ERASURE else b,
                        diff=diff,
                        diffstat=diffstat(diff),
                    )
                )
            elif k not in self.accepted_state:
                # Well then...
                new_bytes = self.output_state[k].value
                assert isinstance(new_bytes, bytes)
                diff = moreorless.unified_diff("", new_bytes.decode(), k)
                changes.append(
                    Modified(
                        rule_name=self.qualname,
                        filename=k,
                        new_bytes=new_bytes,
                        diff=diff,
                        diffstat=diffstat(diff),
                    )
                )

        # Keep only the messages that still apply...
        msgs = []
        disclaimer = None
        rc = set()
        for key_generations, v in self.batch_messages.items():
            if all(self.output_state[k].gens[self.index] == g for k, g in key_generations):
                # Keep, fully applies!
                msgs.append(v[0])
                rc.add(v[1])
            elif not any(self.output_state[k].gens[self.index] == g for k, g in key_generations):
                # Drop, none applies
                pass
            else:
                msgs.append(v[0])
                rc.add(v[1])
                disclaimer = "These messages only partially apply; set to non-eager or batch size of 1 to make more precise\n\n"

        if rc - {99, 0}:
            # Error, consider showing the code...
            self.rule_status = RuleStatus.ERROR
        elif 99 in rc or changes:
            # As documented in ick_protocol, it's a fail if there are changes...
            self.rule_status = RuleStatus.NEEDS_WORK
        else:
            # Success
            self.rule_status = RuleStatus.SUCCESS

        if disclaimer:
            msgs.insert(0, disclaimer)

        if self.rule_status and changes:
            # As documented in ick_protocol, it's a fail if there are changes...
            self.rule_status = RuleStatus.NEEDS_WORK

        changes.append(
            Finished(self.qualname, status=self.rule_status, message="".join(msgs)),
        )
        return changes


def analyze_dir(directory: str, expected: Mapping[str, bytes | Erasure]) -> tuple[set[str], set[str], set[str]]:
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


def match_prefix_patterns(filename: str, prefix: str, patterns: Sequence[str]) -> str | None:
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
        self.command_env: Mapping[str, str] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.rule_config.name!r}>"

    def list(self) -> ListResponse:
        return ListResponse(
            rule_names=[self.rule_config.name],
        )

    def prepare(self) -> bool:
        return True  # no setup required

    def add_steps_to_run(self, projects: Any, env: Mapping[str, str], run: Run[str, bytes | Erasure]) -> None:
        qualname = self.rule_config.qualname

        if self.rule_config.scope == Scope.FILE:
            for p in projects:
                run.add_step(
                    GenericPreparedStep(
                        qualname=qualname,
                        patterns=self.rule_config.inputs,  # Don't default, let it raise
                        project_path=p.subdir,
                        cmdline=self.command_parts,
                        extra_env={**env, **self.command_env},
                        append_filenames=True,
                        rule_prepare=self.prepare,
                    )
                )
        elif self.rule_config.scope == Scope.PROJECT:
            # TODO when nested projects are supported, this can process the
            # same file multiple times; but that's better than not handling
            # project-relative paths.  There's some work to do here once they
            # can nest.
            for p in projects:
                run.add_step(
                    GenericPreparedStep(
                        qualname=qualname,
                        # Default to wanting all files, but allow specifying that
                        # you want _no_ files as empty list.
                        patterns=("*",) if self.rule_config.inputs is None else self.rule_config.inputs,
                        project_path=p.subdir,
                        cmdline=self.command_parts,
                        extra_env={**env, **self.command_env},
                        append_filenames=False,
                        rule_prepare=self.prepare,
                        eager=False,
                        batch_size=9999,  # TODO: -1 once ff 0.8 final is out
                    )
                )
        else:  # REPO
            run.add_step(
                GenericPreparedStep(
                    qualname=qualname,
                    # Default to wanting all files, but allow specifying that
                    # you want _no_ files as empty list.
                    patterns=("*",) if self.rule_config.inputs is None else self.rule_config.inputs,
                    project_path="",
                    cmdline=self.command_parts,
                    extra_env={**env, **self.command_env},
                    append_filenames=False,
                    rule_prepare=self.prepare,
                    eager=False,
                    batch_size=9999,  # TODO: -1 once ff 0.8 final is out
                )
            )
