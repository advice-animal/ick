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
from moreorless.combined import combined_diff
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
        with ThreadPoolExecutor() as tpe:
            print("[dim]testing...[/dim]")
            # It's about this point I realize that yes, I am writing a whole
            # test runner and that's not the business I want to be in.  Oh
            # well...
            buffered_output = io.StringIO()

            i = 0
            for rule_instance, names in self.iter_tests():
                outstanding = {}
                print(f"  [bold]{rule_instance.rule_config.qualname}[/bold]: ", end="")
                rule_instance.prepare()
                if not names:
                    print("<no-test>", end="")
                    print(
                        f"{rule_instance.rule_config.qualname}: [yellow]no tests[/yellow] in {rule_instance.rule_config.test_path}",
                        file=buffered_output,
                    )
                else:
                    key = str(i)
                    i += 1
                    for n in names:
                        outstanding[tpe.submit(self._perform_test, rule_instance, n)] = (
                            key,
                            f"{rule_instance.rule_config.qualname} on {n}",
                        )

                success = True
                for fut in outstanding.keys():
                    progress_key, desc = outstanding[fut]
                    try:
                        fut.result()
                    except Exception as e:
                        print("[red]F[/red]", end="")
                        print(f"  {desc}:", file=buffered_output)
                        # This should be combined with how we actually run
                        # things...
                        typ, value, tb = sys.exc_info()
                        traceback.print_tb(tb, file=buffered_output)
                        # TODO redent
                        print(repr(e), file=buffered_output)
                        success = False
                    else:
                        print(".", end="")

                # TODO try to line these up
                if success:
                    print(" [green]PASS[/green]")
                else:
                    print(" [red]FAIL[/red]")

            if buffered_output.tell():
                print()
                print("FAILING INFO")
                print()
                print(buffered_output.getvalue())
                return 1

            return 0

    def _perform_test(self, rule_instance, test_path) -> None:
        with TemporaryDirectory() as td, ExitStack() as stack:
            tp = Path(td)
            copytree(test_path / "a", tp, dirs_exist_ok=True)

            repo = maybe_repo(tp, stack.enter_context)

            project = Project(repo.root, "", "python", "invalid.bin")
            ap = test_path / "a"
            bp = test_path / "b"
            files_to_check = set(glob("*", root_dir=bp, recursive=True))
            files_to_check.update(glob(".github/**", root_dir=bp, recursive=True))
            files_to_check = {f for f in files_to_check if (bp / f).is_file()}

            response = self._run_one(rule_instance, repo, project)
            if not isinstance(response[-1], Finished):
                raise AssertionError(f"Last response is not Finished: {response[-1].__class__.__name__}")
            if response[-1].error:
                expected_path = bp / "output.txt"
                if not expected_path.exists():
                    raise AssertionError(
                        f"Test crashed, but {expected_path} doesn't exist so that seems unintended:\n" + response[-1].message
                    )

                expected = expected_path.read_text()
                if expected != response[-1].message:
                    print("Testing", test_path)
                    print(moreorless.unified_diff(expected, response[-1].message, "output.txt"))
                    assert False, response[-1].message
                return

            for r in response[:-1]:
                assert isinstance(r, Modified)
                if r.new_bytes is None:
                    assert r.filename not in files_to_check, "missing removal"
                else:
                    assert r.filename in files_to_check, "missing edit"
                    if (bp / r.filename).read_bytes() != r.new_bytes:
                        print(rule_instance.rule_config.name, "fail")
                        print(
                            combined_diff(
                                [(ap / r.filename).read_text()],
                                [(bp / r.filename).read_text(), r.new_bytes.decode()],
                                from_filenames=["original"],
                                to_filenames=["expected", "actual"],
                            )
                        )
                        assert False, f"{r.filename} (modified) differs"
                    files_to_check.remove(r.filename)

            for unchanged_file in files_to_check:
                assert (test_path / "a" / unchanged_file).read_bytes() == (bp / unchanged_file).read_bytes(), (
                    f"{unchanged_file} (unchanged) differs"
                )

    def iter_tests(self):
        # Yields (impl, project_paths) for projects in test dir
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

    def _run_one(self, rule_instance, repo, project):
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
            if not impl.runnable:
                msg += f"  *** {impl.status}"
            for rule in impl.list().rule_names:
                rules_by_urgency[impl.rule_config.urgency].append(msg)

        first = True
        for u, rules in sorted(rules_by_urgency.items()):
            if not first:
                print()
            else:
                first = False

            print(u.name)
            print("=" * len(str(u.name)))
            for v in rules:
                print(f"* {v}")


def pl(noun: str, count: int) -> str:
    if count == 1:
        return noun
    return noun + "s"
