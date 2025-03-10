from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch
from glob import glob
from logging import getLogger
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any

import moreorless.click
from keke import ktrace
from rich.progress import Progress

from ick_protocol import Finished, Modified

from .clone_aside import CloneAside
from .config import HookConfig
from .config.hook_repo import discover_hooks, get_impl
from .project_finder import find_projects
from .sh import run_cmd
from .types_project import Project, Repo

LOG = getLogger(__name__)


class Runner:
    def __init__(self, rtc, repo, explicit_project=None):
        self.rtc = rtc
        self.hooks = discover_hooks(rtc)
        self.repo = repo
        # TODO there's a var on repo to store this...
        self.projects = find_projects(repo, repo.zfiles, self.rtc.main_config)
        assert explicit_project is None
        self.explicit_project = explicit_project

    def iter_hook_impl(self):
        for hook in self.hooks:
            # TODO the isinstance is here because of handling collections,
            # which may be overcomplicating things this early...
            if isinstance(hook, HookConfig):
                if hook.urgency < self.rtc.filter_config.min_urgency:
                    continue
            i = get_impl(hook)(hook, self.rtc)
            yield i

    def selftest(self) -> Any:
        with ThreadPoolExecutor() as tpe, Progress() as progress:
            outstanding = {}
            prepare_key = progress.add_task("Prepare", total=None)
            for hook_instance, names in self.iter_tests():
                hook_instance.prepare()
                progress.update(prepare_key)
                if not names:
                    progress.console.print("no tests under", hook_instance.hook_config.test_path)
                else:
                    key = progress.add_task(hook_instance.hook_config.qualname, total=len(names))
                    for n in names:
                        outstanding[tpe.submit(self._perform_test, hook_instance, n)] = key

            progress.update(prepare_key, completed=True)
            # breakpoint()

            for fut in as_completed(outstanding.keys()):
                progress_key = outstanding[fut]
                try:
                    fut.result()
                except Exception as e:
                    progress.console.print(repr(e))
                else:
                    progress.console.print(progress_key, "ok")
                progress.update(progress_key, advance=1)

    def _perform_test(self, hook_instance, test_path) -> bool:
        with TemporaryDirectory() as td:
            tp = Path(td)
            copytree(test_path / "a", tp, dirs_exist_ok=True)
            run_cmd(["git", "init"], cwd=tp)
            run_cmd(["git", "add", "-N", "."], cwd=tp)
            run_cmd(["git", "commit", "-a", "-m", "init"], cwd=tp)

            repo = Repo(tp)

            project = Project(tp, "", "python", "invalid.bin")
            bp = test_path / "b"
            files_to_check = set(glob("*", root_dir=bp, recursive=True))

            response = self._run_one(hook_instance, repo, project)
            assert isinstance(response[-1], Finished), "Last response is finished"
            if response[-1].error:
                expected = (test_path / "b" / "output.txt").read_text()
                if expected != response[-1].message:
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
                    # print(r.diff)
                    assert (bp / r.filename).read_bytes() == r.new_bytes, f"{r.filename} (modified) differs"
                    files_to_check.remove(r.filename)

            for unchanged_file in files_to_check:
                assert (test_path / "a" / unchanged_file).read_bytes() == (bp / unchanged_file).read_bytes(), (
                    f"{unchanged_file} (unchanged) differs"
                )

    def iter_tests(self):
        # Yields (impl, project_paths) for projects in test dir
        for impl in self.iter_hook_impl():
            if hasattr(impl, "hook_config"):
                test_path = impl.hook_config.test_path
            else:
                print("Test for collections are not implemented")
                continue

            if (test_path / "a").exists():
                yield impl, (test_path,)
            else:
                # Multiple tests have an additional level of directories
                yield impl, tuple(test_path.glob("*/"))

    def run(self) -> Any:
        for impl in self.iter_hook_impl():
            if hasattr(impl, "hook_config"):
                name = impl.hook_config.name
                print(impl.hook_config.test_path)
            else:
                name = repr(impl)

            impl.prepare()
            for p in self.projects:
                responses = self._run_one(impl, self.repo, p)
                print("  ", name, impl, p.subdir)
                for r in responses:
                    if isinstance(r, Modified):
                        print("    ", r.filename, r.diffstat)
                    else:
                        print("    ", r)

    def _run_one(self, hook_instance, repo, project):
        try:
            resp = []
            with CloneAside(repo.root) as tmp:
                with hook_instance.work_on_project(tmp) as work:
                    # TODO multiple hook names (in a collection) happen at once?
                    for h in hook_instance.list().hook_names:
                        # TODO only if files exist
                        # TODO only if files have some contents
                        filenames = repo.zfiles.rstrip("\0").split("\0")
                        assert "" not in filenames
                        # TODO %.py different than *.py once we go parallel
                        if hook_instance.hook_config.inputs:
                            filenames = [f for f in filenames if any(fnmatch(f, x) for x in hook_instance.hook_config.inputs)]

                        resp.extend(work.run("ZZZ", filenames))
        except Exception as e:
            resp = [Finished("ZZZ", error=True, message=repr(e))]
        return resp

    @ktrace()
    def echo_hooks(self) -> None:
        d = {}
        for impl in self.iter_hook_impl():
            impl.prepare()
            for hook in impl.list().hook_names:
                d.setdefault(impl.hook_config.urgency, []).append(hook)

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
