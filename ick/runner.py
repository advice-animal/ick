from __future__ import annotations

import collections
import io
import json
import re
from contextlib import ExitStack
from dataclasses import dataclass
from glob import glob
from logging import getLogger
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable, Sequence

import moreorless
from feedforward import Run, Step
from feedforward.erasure import Erasure  # todo: export this properly from feedforward
from keke import ktrace
from moreorless import unified_diff
from rich import print

from ick_protocol import Finished, Modified, RuleStatus

from .base_rule import BaseRule, GenericPreparedStep
from .config import RuntimeConfig
from .config.rule_repo import discover_rules, get_impl
from .project_finder import find_projects
from .types_project import BaseRepo, Project, Repo, maybe_repo

LOG = getLogger(__name__)


# TODO temporary; this should go in protocol and be better typed...
@dataclass
class HighLevelResult:
    """
    Capture the result of running ick in a structured way.

    rule is the qualified name of the rule
    """

    rule: str
    project: str
    modifications: Sequence[Modified]
    finished: Finished


@dataclass
class TestResult:
    """Capture the result of running a test in a structured way."""

    rule_instance: BaseRule
    test_path: Path
    message: str = ""
    success: bool = False
    diff: str = ""
    traceback: str = ""


class Runner:
    # Strings to replace in outputs while running scenario tests.
    _testing_replacements: dict[str, str] = {}

    def __init__(self, rtc: RuntimeConfig, repo: Repo) -> None:
        self.rtc = rtc
        self.rules = discover_rules(rtc)
        self.repo: BaseRepo = repo
        self.ick_env_vars = {
            "ICK_REPO_PATH": str(repo.root),
        }
        if self.rtc.settings.apply:
            self.ick_env_vars["ICK_APPLY"] = "1"

        # TODO there's a var on repo to store this...
        self.projects: list[Project] = find_projects(repo, repo.zfiles, self.rtc.main_config)

    def iter_rule_impl(self) -> Iterable[BaseRule]:
        name_filter = re.compile(self.rtc.filter_config.name_filter_re).fullmatch
        rules_matched = 0
        for rule in self.rules:
            if rule.urgency < self.rtc.filter_config.min_urgency:
                continue

            if not name_filter(rule.qualname):
                continue

            rules_matched += 1
            yield get_impl(rule)(rule)

        if rules_matched == 0 and len(self.rules) > 0:
            print(
                f"[red]No rules found with urgency '{self.rtc.filter_config.min_urgency.value}' or greater that matches the pattern '{self.rtc.filter_config.name_filter_re}'.[/red]"
            )

    def test_rules(self) -> int:
        """
        Returns an exit code (0 on success)
        """
        print("[dim]testing...[/dim]")
        buffered_output = io.StringIO()

        def buf_print(text: str) -> None:
            """Print to the buffered output.

            This is needed instead of print(..., file=buffered_output) to get
            the rich highlighting correct.
            """
            buffered_output.write(text)
            buffered_output.write("\n")

        # Run is already parallel, so execute this singly so we can operate on
        # self's instance vars.

        final_status = 0
        for rule_instance, test_paths in self.iter_tests():
            success = True
            print(f"  [bold]{rule_instance.rule_config.qualname}[/bold]: ", end="")
            if not test_paths:
                print("<no-test>", end="")
                buf_print(
                    f"{rule_instance.rule_config.qualname}: [yellow]no tests[/yellow] in {rule_instance.rule_config.test_path}",
                )
            else:
                for test_path in sorted(test_paths):
                    result = TestResult(rule_instance, test_path)
                    # Not guarded because in user code won't raise here, it
                    # will surface as a HLR failure.
                    self._perform_test(rule_instance, test_path, result)

                    if result.success:
                        print(".", end="")
                    else:
                        success = False
                        final_status = 1
                        print("[red]F[/]", end="")
                        buf_print(f"{'-' * 80}")
                        rule_test_path = result.rule_instance.rule_config.test_path
                        assert rule_test_path is not None
                        rel_test_path = result.test_path.relative_to(rule_test_path)
                        with_test = ""
                        if str(rel_test_path) != ".":
                            with_test = f" with [bold]{rel_test_path}[/]"
                        buf_print(f"testing [bold]{rule_instance.rule_config.qualname}[/]{with_test}:")
                        buf_print(result.traceback)
                        buf_print(result.message)
                        buf_print(result.diff)

            if success:
                print(" [green]PASS[/]")
            else:
                print(" [red]FAIL[/]")

        if buffered_output.tell():
            print()
            print("DETAILS")
            print(buffered_output.getvalue())

        return final_status

    def _perform_test(self, rule_instance: BaseRule, test_path: Path, result: TestResult) -> None:
        inp = test_path / "input"
        outp = test_path / "output"
        if not inp.exists():
            result.message = f"Test input directory {inp} is missing"
            return
        if not outp.exists():
            result.message = f"Test output directory {outp} is missing"
            return

        with TemporaryDirectory() as td, ExitStack() as stack:
            tp = Path(td)
            copytree(inp, tp, dirs_exist_ok=True)

            repo = maybe_repo(tp, stack.enter_context, for_testing=True)

            run = next(iter(self.run(test_impl=rule_instance, test_repo=repo)))
            response = run.modifications

            files_to_check = set(glob("**", root_dir=outp, recursive=True, include_hidden=True))
            files_to_check = {f for f in files_to_check if (outp / f).is_file()} - {"output.txt", "error.txt"}

            actual_output = run.finished.message
            for old, new in self._testing_replacements.items():
                actual_output = actual_output.replace(old, new)

            if run.finished.status is RuleStatus.ERROR:
                # Error state
                expected_path = outp / "error.txt"
                if not expected_path.exists():
                    result.message = f"Test crashed, but {expected_path} doesn't exist so that seems unintended:\n{actual_output}"
                    return

                expected = expected_path.read_text()
                if expected == actual_output:
                    result.success = True
                else:
                    result.diff = moreorless.unified_diff(expected, actual_output, "error.txt")
                    result.message = "Different output found"
                return
            elif run.finished.status is RuleStatus.NEEDS_WORK and not run.modifications:
                # Didn't match expectation
                expected_path = outp / "output.txt"
                if not expected_path.exists():
                    result.message = f"Test failed, but {expected_path} doesn't exist so that seems unintended:\n{actual_output}"
                    return

                expected = expected_path.read_text()
                if expected == actual_output:
                    result.success = True
                else:
                    result.diff = moreorless.unified_diff(expected, actual_output, "output.txt")
                    result.message = "Different output found"
                return
            else:
                # Mainly 0 exit
                for r in response:
                    assert isinstance(r, Modified)
                    if r.new_bytes is None:
                        if r.filename in files_to_check:
                            result.message = f"Missing removal of {r.filename!r}"
                            return
                    else:
                        if r.filename not in files_to_check:
                            result.message = f"Unexpected new file: {r.filename!r}"
                            return
                        outf = outp / r.filename
                        if outf.read_bytes() != r.new_bytes:
                            result.diff = unified_diff(
                                outf.read_text(),
                                r.new_bytes.decode(),
                                r.filename,
                            )
                            result.message = f"{r.filename!r} (modified) differs"
                            return
                        files_to_check.remove(r.filename)

                for unchanged_file in files_to_check:
                    if (inp / unchanged_file).read_bytes() != (outp / unchanged_file).read_bytes():
                        result.message = f"{unchanged_file!r} (unchanged) differs"
                        return

        result.success = True

    def iter_tests(self) -> Iterable[tuple[BaseRule, tuple[Path, ...]]]:
        # Yields (impl, test_paths) for projects in test dir
        for impl in self.iter_rule_impl():
            test_path = impl.rule_config.test_path
            assert test_path is not None
            yield impl, tuple(test_path.glob("*/"))

    def run(
        self,
        *,
        test_impl: BaseRule | None = None,
        test_repo: BaseRepo | None = None,
        status_callback: Callable[[Run[Any, Any]], None] | None = None,
        done_callback: Callable[[Run[Any, Any]], None] | None = None,
    ) -> Iterable[HighLevelResult]:
        # TODO deliberate in a flag:
        run: Run[str, bytes | Erasure] = Run(status_callback=status_callback, done_callback=done_callback)
        if test_impl:
            assert test_repo
            self.repo = test_repo
            project = Project(test_repo, "", "python", "invalid.bin")
            test_impl.add_steps_to_run([project], self.ick_env_vars, run)
        else:
            for impl in self.iter_rule_impl():
                impl.add_steps_to_run(self.projects, self.ick_env_vars, run)

        run.add_step(Step())  # Final sink

        # TODO parallelize or show a progress bar, this takes a while...
        repo_contents: dict[str, bytes | Erasure] = {}
        # TODO the version that includes dirty files
        for f in sorted(self.repo.zfiles.split("\0")):
            if not f:
                continue
            p = self.repo.root / f
            # TODO symlinks, empty dirs?
            if p.is_file():
                repo_contents[f] = p.read_bytes()

        run.run_to_completion(repo_contents)
        for s in run._steps[:-1]:
            assert isinstance(s, GenericPreparedStep)
            if s.cancelled:
                # This should also encompass exit codes other than 0 and 99
                # print(f"{s} failed:")
                # print(f"  {s.cancel_reason}")
                yield HighLevelResult(s.qualname, s.match_prefix, [], Finished("a", RuleStatus.NEEDS_WORK, s.cancel_reason))
            else:
                # if any(e == 99 for e in s.exit_codes):
                #     ...

                changes = s.compute_diff_messages()
                yield HighLevelResult(s.qualname, s.match_prefix, changes[:-1], changes[-1])

    @ktrace()
    def echo_rules(self) -> None:
        rules_by_urgency = collections.defaultdict(list)
        for impl in self.iter_rule_impl():
            impl.prepare()

            msg = f"[bold]{impl.rule_config.qualname}[/]"
            if impl.rule_config.description:
                msg += f": {impl.rule_config.description}"
            if not impl.runnable:
                msg += f"  *** {impl.status}"
            for rule in impl.list().rule_names:
                rules_by_urgency[impl.rule_config.urgency].append(msg)

        first = True
        for urgency_label, rules in sorted(rules_by_urgency.items(), reverse=True):
            if not first:
                print()
            else:
                first = False

            print(f"[bold]{urgency_label.name}[/]")
            print("=" * len(str(urgency_label.name)))
            for rule in rules:
                print(f"* {rule}")

    @ktrace()
    def echo_rules_json(self) -> None:
        rules = {}
        for impl in self.iter_rule_impl():
            impl.prepare()
            config = impl.rule_config
            rule = {
                "duration": config.hours,
                "description": config.description,
                "urgency": str(config.urgency.name),
                "risk": str(config.risk.name),
                "contact": config.contact,
                "url": config.url,
            }
            rules[config.qualname] = rule

        print(json.dumps({"rules": rules}, indent=4))


def pl(noun: str, count: int) -> str:
    if count == 1:
        return noun
    return noun + "s"


def _demo_status_callback(run: Run[str, bytes]) -> None:
    print("%4d/%4d " % (run._finalized_idx + 1, len(run._steps)) + " ".join(step.emoji() for step in run._steps))


def _demo_done_callback(run: Run[str, bytes]) -> None:
    print(" " * 10 + " ".join("%2d" % (next(step.gen_counter) - 1) for step in run._steps))
    print(f"Total time: {run._end_time - run._start_time:.2f}s")
