from __future__ import annotations

import collections
import io
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from fnmatch import fnmatch
from glob import glob
from logging import getLogger
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any, Iterable

import moreorless
from keke import ktrace
from moreorless import unified_diff
from rich import print

from ick_protocol import Finished, Modified

from .base_rule import BaseRule
from .clone_aside import CloneAside
from .config.rule_repo import discover_rules, get_impl
from .project_finder import find_projects
from .types_project import Project, maybe_repo

LOG = getLogger(__name__)


# TODO temporary; this should go in protocol and be better typed...
@dataclass
class HighLevelResult:
    rule: Any
    project: Any
    modifications: Any
    finished: Any


@dataclass
class TestResult:
    """Capture the result of running a test in a structured way."""

    rule_instance: BaseRule
    test_path: str
    message: str = ""
    success: bool = False
    diff: str = ""
    traceback: str = ""


class Runner:
    def __init__(self, rtc, repo, explicit_project=None):
        self.rtc = rtc
        self.rules = discover_rules(rtc)
        self.repo = repo
        # TODO there's a var on repo to store this...
        self.projects: list[Project] = find_projects(repo, repo.zfiles, self.rtc.main_config)
        assert explicit_project is None
        self.explicit_project = explicit_project

    def iter_rule_impl(self) -> Iterable[BaseRule]:
        name_filter = re.compile(self.rtc.filter_config.name_filter_re).fullmatch
        for rule in self.rules:
            if rule.urgency < self.rtc.filter_config.min_urgency:
                continue
            if not name_filter(rule.qualname):
                continue

            i = get_impl(rule)(rule, self.rtc)
            yield i

    def test_rules(self) -> int:
        """
        Returns an exit code (0 on success)
        """
        print("[dim]testing...[/dim]")
        buffered_output = io.StringIO()

        def buf_print(text):
            """Print to the buffered output.

            This is needed instead of print(..., file=buffered_output) to get
            the rich highlighting correct.
            """
            buffered_output.write(text)
            buffered_output.write("\n")

        with ThreadPoolExecutor() as tpe:
            for rule_instance, test_paths in self.iter_tests():
                outstanding = {}
                print(f"  [bold]{rule_instance.rule_config.qualname}[/bold]: ", end="")
                rule_instance.prepare()
                if not test_paths:
                    print("<no-test>", end="")
                    buf_print(
                        f"{rule_instance.rule_config.qualname}: [yellow]no tests[/yellow] in {rule_instance.rule_config.test_path}",
                    )
                else:
                    for test_path in test_paths:
                        result = TestResult(rule_instance, test_path)
                        fut = tpe.submit(self._perform_test, rule_instance, test_path, result)
                        outstanding[fut] = result

                success = True
                for fut in outstanding.keys():
                    result = outstanding[fut]
                    try:
                        fut.result()
                    except Exception as e:
                        result.success = False
                        typ, value, tb = sys.exc_info()
                        # This should be combined with how we actually run things...
                        result.traceback = "".join(traceback.format_tb(tb))
                        result.message = repr(e)

                    if result.success:
                        print(".", end="")
                    else:
                        success = False
                        print("[red]F[/]", end="")
                        buf_print(f"{'-' * 80}")
                        rel_test_path = result.test_path.relative_to(result.rule_instance.rule_config.test_path)
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
                print("FAILING INFO")
                print(buffered_output.getvalue())
                return 1

            return 0

    def _perform_test(self, rule_instance, test_path, result: TestResult) -> None:
        with TemporaryDirectory() as td, ExitStack() as stack:
            tp = Path(td)
            copytree(test_path / "a", tp, dirs_exist_ok=True)

            repo = maybe_repo(tp, stack.enter_context)

            project = Project(repo.root, "", "python", "invalid.bin")
            bp = test_path / "b"
            files_to_check = set(glob("**", root_dir=bp, recursive=True, include_hidden=True))
            files_to_check = {f for f in files_to_check if (bp / f).is_file()}

            response = self._run_one(rule_instance, repo, project)
            if not isinstance(response[-1], Finished):
                raise AssertionError(f"Last response is not Finished: {response[-1].__class__.__name__}")
            if response[-1].error:
                expected_path = bp / "output.txt"
                if not expected_path.exists():
                    result.message = f"Test crashed, but {expected_path} doesn't exist so that seems unintended:\n{response[-1].message}"
                    return

                expected = expected_path.read_text()
                if expected == response[-1].message:
                    result.success = True
                else:
                    result.diff = moreorless.unified_diff(expected, response[-1].message, "output.txt")
                    result.message = "Different output found"
                return

            for r in response[:-1]:
                assert isinstance(r, Modified)
                if r.new_bytes is None:
                    if r.filename in files_to_check:
                        result.message = f"Missing removal of {r.filename!r}"
                        return
                else:
                    if r.filename not in files_to_check:
                        result.message = f"Unexpected new file: {r.filename!r}"
                        return
                    bf = bp / r.filename
                    if bf.read_bytes() != r.new_bytes:
                        result.diff = unified_diff(
                            bf.read_text(),
                            r.new_bytes.decode(),
                            r.filename,
                        )
                        result.message = f"{r.filename!r} (modified) differs"
                        return
                    files_to_check.remove(r.filename)

            for unchanged_file in files_to_check:
                if (test_path / "a" / unchanged_file).read_bytes() != (bp / unchanged_file).read_bytes():
                    result.message = f"{unchanged_file!r} (unchanged) differs"
                    return

        result.success = True

    def iter_tests(self) -> Iterable[tuple[BaseRule, tuple[str, ...]]]:
        # Yields (impl, test_paths) for projects in test dir
        for impl in self.iter_rule_impl():
            if hasattr(impl, "rule_config"):
                test_path = impl.rule_config.test_path
            else:
                print("Test for collections are not implemented")
                continue

            if (test_path / "a").exists():
                yield impl, (test_path,)
            else:
                # Multiple tests have an additional level of directories
                yield impl, tuple(test_path.glob("*/"))

    def run(self) -> Iterable[HighLevelResult]:
        for impl in self.iter_rule_impl():
            qualname = impl.rule_config.qualname

            impl.prepare()
            for p in self.projects:
                responses = self._run_one(impl, self.repo, p)
                mod = [m for m in responses if isinstance(m, Modified)]
                assert isinstance(responses[-1], Finished)
                yield HighLevelResult(qualname, p.subdir, mod, responses[-1])

    def _run_one(self, rule_instance, repo, project) -> list[HighLevelResult]:
        try:
            resp = []
            with CloneAside(repo.root) as tmp:
                with rule_instance.work_on_project(tmp) as work:
                    # TODO multiple rule names (in a collection) happen at once?
                    for h in rule_instance.list().rule_names:
                        # TODO only if files exist
                        # TODO only if files have some contents
                        filenames = repo.zfiles.rstrip("\0").split("\0")
                        assert "" not in filenames
                        # TODO %.py different than *.py once we go parallel
                        if rule_instance.rule_config.inputs:
                            filenames = [f for f in filenames if any(fnmatch(f, x) for x in rule_instance.rule_config.inputs)]

                        resp.extend(work.run(rule_instance.rule_config.qualname, filenames))
        except Exception as e:
            typ, value, tb = sys.exc_info()
            buf = io.StringIO()
            traceback.print_tb(tb, file=buf)
            print(repr(e), file=buf)
            resp = [Finished(rule_instance.rule_config.qualname, error=True, message=buf.getvalue())]
        return resp

    @ktrace()
    def echo_rules(self) -> None:
        rules_by_urgency = collections.defaultdict(list)
        for impl in self.iter_rule_impl():
            impl.prepare()
            duration = ""
            # if impl.rule_config.hours != 1:
            #     duration = f" ({impl.rule_config.hours} {pl('hour', impl.rule_config.hours)})"

            msg = f"{impl.rule_config.qualname}{duration}"
            if impl.rule_config.description:
                msg += f": {impl.rule_config.description}"
            if not impl.runnable:
                msg += f"  *** {impl.status}"
            for rule in impl.list().rule_names:
                rules_by_urgency[impl.rule_config.urgency].append(msg)

        first = True
        for urgency_label, rules in sorted(rules_by_urgency.items()):
            if not first:
                print()
            else:
                first = False

            print(urgency_label.name)
            print("=" * len(str(urgency_label.name)))
            for rule in rules:
                print(f"* {rule}")


def pl(noun: str, count: int) -> str:
    if count == 1:
        return noun
    return noun + "s"
