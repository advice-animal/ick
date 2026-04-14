from __future__ import annotations

import json
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
from .util import diffstat, merge_dicts

LOG = getLogger(__name__)


def materialize(path: str, filename: str, contents: bytes) -> None:
    Path(path, filename).parent.mkdir(exist_ok=True, parents=True)
    Path(path, filename).write_bytes(contents)


class GenericPreparedStep(Step[str, bytes | Erasure]):
    """
    Subclass of step that ensures some setup is complete before processing items.

    Since most steps will need to do some sort of installation (or at least
    checking for prereqs), and we want that to happen once, this calls
    `rule_prepare()` before processing each batch.

    Note: `rule_prepare` is passed in as a function because a Rule might be
    able to do a single setup to perform multiple Steps (if there are multiple
    projects).
    """

    def __init__(
        self,
        qualname: str,
        patterns: Sequence[str],
        project_path: str,
        cmdline: Sequence[str | Path],
        extra_env: dict[str, str],
        append_filenames: bool,
        rule_prepare: Callable[[], bool] | None = None,
        excluded_project_dirs: Sequence[str] = (),
        prefix: str = "",
        exclude_patterns: Sequence[str] = (),
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.qualname = qualname
        self.prefix = prefix
        # TODO figure out how extra_inputs factors in
        assert patterns is not None, "File scoped rules require an `inputs` section in the rule config!"
        self.patterns = patterns
        self.exclude_patterns = exclude_patterns
        self.match_prefix = project_path
        self.matches_at_least_once = False
        self.cmdline = cmdline
        self.extra_env = extra_env
        self.append_filenames = append_filenames
        self.rule_prepare = rule_prepare
        self.excluded_project_dirs = tuple(excluded_project_dirs)
        # dict key is gen, (keys, ...) and for these to match precisely we
        # should have output_state gens[self.index] == gen for all the listed
        # keys; if we have none of them then we should skip that message.
        #
        # dict value is output, exit code and we decide what the aggregate code
        # is at the end.
        self.batch_messages: dict[tuple[tuple[str, int], ...], tuple[str, int, dict[str, Any] | None]] = {}
        self.rule_status = RuleStatus.SUCCESS

    def _key_is_excluded(self, key: str) -> bool:
        for excluded_dir in self.excluded_project_dirs:
            excluded_dir = excluded_dir.rstrip("/")
            if key == excluded_dir or key.startswith(f"{excluded_dir}/"):
                return True
        return False

    def _output_key(self, relative_filename: str) -> str:
        return f"{self.match_prefix}{relative_filename}" if self.match_prefix else relative_filename

    def _ensure_allowed_key(self, key: str) -> bool:
        if self._key_is_excluded(key):
            self.cancel(f"Produced output for excluded project path: {key!r}")
            return False
        return True

    def match(self, key: str) -> bool:
        if self._key_is_excluded(key):
            return False
        m = bool(match_prefix_patterns(key, self.match_prefix, self.patterns))
        if m and self.exclude_patterns:
            filename = key[len(self.match_prefix):].lstrip("/")
            m = not any(fnmatch(filename, pat) for pat in self.exclude_patterns)
        self.matches_at_least_once |= m
        return m

    def run_next_batch(self) -> bool:
        """
        Runs a batch only after there are matches and we're prepared.

        Some files matching the input patterns for a rule must exist in order
        for the Step to do any work.  Because `prepare` and `rule_prepare` are ick
        concepts, we override the parent implementation with one that only does that
        (potentially expensive) setup if input patterns are known to match.

        See note on `Rule.prepare` for the return value expected for
        `rule_prepare` -- in particular, we'll call that quite often and it should just
        cache and return True once ready.
        """
        if self.matches_at_least_once and self.rule_prepare:
            try:
                if not self.rule_prepare():
                    # Important: rules that have a prepare should ensure that only one
                    # thread is preparing at a time (all others should temporarily
                    # return False).

                    # If _we_ got a False from rule_prepare, we also return False which
                    # signals feedforward to keep looking for work elsewhere...
                    return False
            except subprocess.SubprocessError as e:
                if isinstance(e, subprocess.CalledProcessError) and (e.stdout or e.stderr):
                    msg = (e.stdout or "") + (e.stderr or "")
                else:
                    msg = str(e)
                self.cancel(msg)
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
        with TemporaryDirectory() as d, TemporaryDirectory() as output_dir:
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
            env["ICK_OUTPUT_DIR"] = output_dir

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

            outputs: list[Notification[str, bytes | Erasure]] = []
            for n in notifications:
                relative_filename = n.key[len(self.match_prefix) :]
                if relative_filename in changed:
                    key = n.key
                    if not self._ensure_allowed_key(key):
                        return
                    outputs.append(self.update_notification(n, next_gen, new_value=Path(d, relative_filename).read_bytes()))
                    batch_key[n.key] = next_gen
                elif relative_filename in remv:
                    key = n.key
                    if not self._ensure_allowed_key(key):
                        return
                    outputs.append(self.update_notification(n, next_gen, new_value=ERASURE))
                    batch_key[n.key] = next_gen

            brand_new_gens = self.update_generations((0,) * len(notifications[0].state.gens), next_gen)
            for name in new:
                full_key = self._output_key(name)
                if not self._ensure_allowed_key(full_key):
                    return
                batch_key[full_key] = next_gen
                outputs.append(
                    Notification(
                        key=full_key,
                        state=State(
                            gens=brand_new_gens,
                            value=Path(d, name).read_bytes(),
                        ),
                    )
                )

            metadata_path = Path(output_dir) / "metadata.json"
            batch_metadata: dict[str, Any] | None = None
            if metadata_path.exists():
                batch_metadata = json.loads(metadata_path.read_text())

            if batch_value:
                self.batch_messages[tuple(batch_key.items())] = (batch_value[0], batch_value[1], batch_metadata)

            yield from outputs

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
                    try:
                        diff = moreorless.unified_diff(a.decode(), b.decode(), k)
                        diff_stat = diffstat(diff)
                    except UnicodeDecodeError:
                        diff = f"Binary files differ: {k!r} (before: {len(a)} bytes, after: {len(b)} bytes)\n"
                        diff_stat = None
                elif a is ERASURE:
                    # Should really say /dev/null input
                    assert isinstance(b, bytes)
                    try:
                        diff = moreorless.unified_diff("", b.decode(), k)
                        diff_stat = diffstat(diff)
                    except UnicodeDecodeError:
                        diff = f"Binary file created: {k!r} (after: {len(b)} bytes)\n"
                        diff_stat = None
                else:
                    # Should really say /dev/null output
                    try:
                        diff = moreorless.unified_diff(a.decode(), "", k)
                        diff_stat = diffstat(diff)
                    except UnicodeDecodeError:
                        diff = f"Binary file removed: {k!r} (before: {len(a)} bytes)\n"
                        diff_stat = None

                changes.append(
                    Modified(
                        rule_name=self.qualname,
                        filename=k,
                        new_bytes=None if b is ERASURE else b,
                        diff=diff,
                        diffstat=diff_stat,
                    )
                )
            elif k not in self.accepted_state:
                # Well then...
                new_bytes = self.output_state[k].value
                assert isinstance(new_bytes, bytes)
                try:
                    diff = moreorless.unified_diff("", new_bytes.decode(), k)
                    diff_stat = diffstat(diff)
                except UnicodeDecodeError:
                    diff = f"Binary file created: {k!r} (after: {len(new_bytes)} bytes)\n"
                    diff_stat = None
                changes.append(
                    Modified(
                        rule_name=self.qualname,
                        filename=k,
                        new_bytes=new_bytes,
                        diff=diff,
                        diffstat=diff_stat,
                    )
                )

        # Keep only the messages and metadata that still apply...
        msgs = []
        disclaimer = None
        rc = set()
        metadata: dict[str, Any] | None = None
        for key_generations, v in self.batch_messages.items():
            if all(self.output_state[k].gens[self.index] == g for k, g in key_generations):
                # Keep, fully applies!
                msgs.append(v[0])
                rc.add(v[1])
                metadata = merge_dicts(metadata, v[2])
            elif not any(self.output_state[k].gens[self.index] == g for k, g in key_generations):
                # Drop, none applies
                pass
            else:
                msgs.append(v[0])
                rc.add(v[1])
                metadata = merge_dicts(metadata, v[2])
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
            Finished(self.qualname, status=self.rule_status, message="".join(msgs), metadata=metadata),
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
        """
        Make sure that we're ready to process items.

        This will always be called from a worker thread, so it's perfectly fine
        to do a core's worth of work in this thread without exceeding the
        overall budget, or any arbitrary work as long as it's infrequent and
        can handle a thundering herd.

        Nontrivial uses will typically involve a fast path and a lock to ensure
        the setup only happens once, and the thread either checking or setting
        up will block before returning true.  See `ick/venv.py` for an example.

        Return value:

            True: ready to go (potentially after blocking)
            False: not ready (find some other work to do)

        """
        return True  # no setup required

    def add_steps_to_run(self, projects: Any, env: Mapping[str, str], run: Run[str, bytes | Erasure]) -> None:
        qualname = self.rule_config.qualname
        prefix = self.rule_config.prefix
        name_in_repo = self.rule_config.name_in_repo

        if self.rule_config.scope == Scope.FILE:
            for p in projects:
                if self.rule_config.project_types is not None and p.typ not in self.rule_config.project_types:
                    continue
                if name_in_repo in p.config.ignore_rules:
                    continue
                excluded_project_dirs = tuple(q.subdir for q in projects if q.subdir != p.subdir and q.subdir.startswith(p.subdir))
                per_rule = p.config.rules.get(name_in_repo)
                run.add_step(
                    GenericPreparedStep(
                        qualname=qualname,
                        patterns=self.rule_config.inputs,  # Don't default, let it raise
                        project_path=p.subdir,
                        cmdline=self.command_parts,
                        extra_env={**env, **self.command_env},
                        append_filenames=True,
                        rule_prepare=self.prepare,
                        excluded_project_dirs=excluded_project_dirs,
                        prefix=prefix,
                        exclude_patterns=per_rule.exclude_filenames if per_rule else (),
                        batch_size=self.rule_config.batch_size,
                    )
                )
        elif self.rule_config.scope == Scope.PROJECT:
            # TODO when nested projects are supported, this can process the
            # same file multiple times; but that's better than not handling
            # project-relative paths.  There's some work to do here once they
            # can nest.
            for p in projects:
                if self.rule_config.project_types is not None and p.typ not in self.rule_config.project_types:
                    continue
                if name_in_repo in p.config.ignore_rules:
                    continue
                excluded_project_dirs = tuple(q.subdir for q in projects if q.subdir != p.subdir and q.subdir.startswith(p.subdir))
                per_rule = p.config.rules.get(name_in_repo)
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
                        excluded_project_dirs=excluded_project_dirs,
                        prefix=prefix,
                        exclude_patterns=per_rule.exclude_filenames if per_rule else (),
                        eager=False,
                        batch_size=-1,
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
                    prefix=prefix,
                    eager=False,
                    batch_size=-1,
                )
            )
