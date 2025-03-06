"""
Clones a local git repo, making a commit at the end.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

from keke import ktrace

from .device_tmpdir import find_tmpdir
from .git import head
from .sh import run_cmd

LOG = getLogger(__name__)


class CloneAside:
    def __init__(self, orig_path: Path) -> None:
        self.orig_path = Path(orig_path)
        self.head_commit, rc = run_cmd(["git", "rev-parse", "HEAD"], cwd=orig_path)
        self.head_commit = self.head_commit.strip()
        self.head = head(orig_path)
        self.td = TemporaryDirectory(dir=find_tmpdir(self.orig_path))

    @ktrace()
    def __enter__(self):
        tdp = self.td.__enter__()

        # do clone (defaults to HEAD)
        run_cmd(["git", "clone", "--single-branch", "--depth", "1", "--no-tags", "--local", self.orig_path, tdp])
        # run_cmd(["git", "init"], cwd=tdp)
        # run_cmd(["git", "remote", "add", "origin", self.orig_path], cwd=tdp)
        # run_cmd(["git", "fetch", "--no-tags", "origin", self.head], cwd=tdp)
        # run_cmd(["git", "checkout", self.head], cwd=tdp)
        # sync modified files
        modified_and_staged_diff, rc = run_cmd(["git", "diff", "HEAD"], cwd=self.orig_path)
        if modified_and_staged_diff:
            run_cmd(["git", "apply"], cwd=tdp, input=modified_and_staged_diff)

        # sync untracked files
        untracked_files_diff, rc = run_cmd(
            [
                "/bin/sh",
                "-c",
                "git ls-files --others --exclude-standard -z | xargs -0 -n 1 --no-run-if-empty git --no-pager diff --no-exit-code /dev/null",
            ],
            cwd=self.orig_path,
            check=False,  # Seems to return 123 on diff
        )
        if untracked_files_diff:
            run_cmd(["git", "apply"], cwd=tdp, input=untracked_files_diff)

        # mark intent-to-add
        run_cmd(["git", "add", "-N", "."], cwd=tdp)

        # commit
        run_cmd(["git", "commit", "-a", "-m", "sync-wc"], cwd=tdp, check=False)
        # either find that last commit, or the original one
        sync_commit, rc = run_cmd(["git", "rev-parse", "HEAD"], cwd=tdp)
        self.sync_commit = sync_commit.strip()

        return tdp

    @ktrace()
    def __exit__(self, *args):
        self.td.__exit__(*args)


if __name__ == "__main__":
    from keke import TraceOutput
    # basicConfig(level=DEBUG)

    with TraceOutput(file=open("trace.out", "w")):
        with CloneAside(Path.cwd()):
            pass
