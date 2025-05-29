from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch
from glob import glob
from logging import getLogger
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any

import moreorless
from keke import ktrace
from moreorless.click import echo_color_precomputed_diff
from moreorless.combined import combined_diff
from rich.progress import Progress

from ick_protocol import Finished, Modified

from .clone_aside import CloneAside
from .config.rule_repo import discover_rules, get_impl
from .project_finder import find_projects
from .sh import run_cmd
from .types_project import Project, Repo

LOG = getLogger(__name__)


class Runner:
    def __init__(self, rtc, repo, explicit_project=None):
        self.rtc = rtc
        self.rules = discover_rules(rtc)
        self.repo = repo
        # TODO there's a var on repo to store this...
        self.projects: list[Project] = find_projects(repo, repo.zfiles, self.rtc.main_config)
        assert explicit_project is None
        self.explicit_project = explicit_project

    def iter_rule_impl(self):
        name_filter = re.compile(self.rtc.filter_config.name_filter_re).fullmatch
        for rule in self.rules:
            if rule.urgency < self.rtc.filter_config.min_urgency:
                continue
            if not name_filter(rule.qualname):
                continue

            i = get_impl(rule)(rule, self.rtc)
            yield i

    def test_rules(self) -> Any:
        with ThreadPoolExecutor() as tpe, Progress() as progress:
            outstanding = {}
            prepare_key = progress.add_task("Prepare", total=None)
            for rule_instance, names in self.iter_tests():
                rule_instance.prepare()
                progress.update(prepare_key)
                if not names:
                    progress.console.print("no tests for", rule_instance.rule_config.qualname, "under", rule_instance.rule_config.test_path)
                else:
                    key = progress.add_task(rule_instance.rule_config.qualname, total=len(names))
                    for n in names:
                        outstanding[tpe.submit(self._perform_test, rule_instance, n)] = (key, rule_instance.rule_config.qualname)

            progress.update(prepare_key, completed=True)
            # breakpoint()

            for fut in as_completed(outstanding.keys()):
                progress_key, desc = outstanding[fut]
                try:
                    fut.result()
                except Exception as e:
                    progress.console.print(desc)
                    progress.console.print("  " + repr(e))
                else:
                    progress.console.print(progress_key, "ok")
                progress.update(progress_key, advance=1)

    def _perform_test(self, rule_instance, test_path) -> bool:
        with TemporaryDirectory() as td:
            tp = Path(td)
            copytree(test_path / "a", tp, dirs_exist_ok=True)
            run_cmd(["git", "init"], cwd=tp)
            run_cmd(["git", "add", "-N", "."], cwd=tp)
            run_cmd(["git", "commit", "-a", "-m", "init"], cwd=tp)

            repo = Repo(tp)

            project = Project(tp, "", "python", "invalid.bin")
            ap = test_path / "a"
            bp = test_path / "b"
            files_to_check = set(glob("*", root_dir=bp, recursive=True))

            response = self._run_one(rule_instance, repo, project)
            assert isinstance(response[-1], Finished), "Last response is finished"
            if response[-1].error:
                expected_path = bp / "output.txt"
                if not expected_path.exists():
                    assert False, response[-1].message

                expected = expected_path.read_text()
                if expected != response[-1].message:
                    print("Testing", test_path)
                    print(moreorless.unified_diff(expected, response[-1].message, "output.txt"))
                    assert False, response[-1].message
                return

            assert not response[-1].error, response[-1].message

            for r in response[:-1]:
                assert isinstance(r, Modified)
                if r.new_bytes is None:
                    assert r.filename not in files_to_check
                else:
                    assert r.filename in files_to_check
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

    def run(self) -> Any:
        for impl in self.iter_rule_impl():
            qualname = impl.rule_config.qualname

            impl.prepare()
            for p in self.projects:
                responses = self._run_one(impl, self.repo, p)
                print("  ", qualname, impl, p.subdir)
                for r in responses:
                    if isinstance(r, Modified):
                        print("    ", r.filename, r.diffstat)
                        echo_color_precomputed_diff(r.diff)
                    elif isinstance(r, Finished) and r.error:
                        for line in r.message.splitlines():
                            print("    ", line)
                    else:
                        print("    ", r)

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
            resp = [Finished(rule_instance.rule_config.qualname, error=True, message=repr(e))]
        return resp

    @ktrace()
    def echo_rules(self) -> None:
        d = {}
        for impl in self.iter_rule_impl():
            impl.prepare()
            duration = ""
            # if impl.rule_config.hours != 1:
            #     duration = f" ({impl.rule_config.hours} {pl('hour', impl.rule_config.hours)})"

            for rule in impl.list().rule_names:
                d.setdefault(impl.rule_config.urgency, []).append(f"{impl.rule_config.qualname}{duration}")

        first = True
        for u in sorted(d.keys()):
            if not first:
                print()
            else:
                first = False

            print(u.name)
            print("=" * len(str(u.name)))
            for v in d[u]:
                print(f"* {v}")


def pl(noun: str, count: int) -> str:
    if count == 1:
        return noun
    return noun + "s"
