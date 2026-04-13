from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp
from typing import Sequence

from .sh import run_cmd, run_cmd_status


def check_clean_tree(repo_root: Path) -> bool:
    """Return True if working tree is clean (no staged or unstaged changes)."""
    output, _ = run_cmd_status(["git", "status", "--porcelain"], cwd=repo_root, check=False)
    return output.strip() == ""


def create_worktree_branch(repo_root: Path, branch_name: str) -> Path:
    """Create a new branch in a temporary worktree; return the worktree path."""
    wt_path = Path(mkdtemp(prefix="ick-commit-"))
    # mkdtemp creates the dir; git worktree add requires it to not exist (or be empty)
    # Use rmdir + let git recreate it, or use a path that doesn't exist yet
    wt_path.rmdir()
    run_cmd(["git", "worktree", "add", "-b", branch_name, str(wt_path)], cwd=repo_root)
    return wt_path


def remove_worktree(repo_root: Path, wt_path: Path) -> None:
    """Remove a git worktree."""
    run_cmd(["git", "worktree", "remove", "--force", str(wt_path)], cwd=repo_root)


def apply_and_commit(work_dir: Path, modifications: Sequence, message: str) -> str:
    """Apply file modifications, stage them, and create a commit. Returns short SHA."""
    for mod in modifications:
        path = work_dir / mod.filename
        if mod.new_bytes is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(mod.new_bytes)
    filenames = [mod.filename for mod in modifications]
    run_cmd(["git", "add", "--"] + filenames, cwd=work_dir)
    run_cmd(["git", "commit", "-m", message], cwd=work_dir)
    return run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=work_dir).strip()
