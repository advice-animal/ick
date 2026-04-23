from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Generator

from vmodule import VLOG_1, VLOG_2

LOG = getLogger(__name__)


def parse_diff_stat(s: str | None) -> int:
    """Convert a diffstat string like '+3-2' to total lines changed."""
    if not s:
        return 0
    return sum(abs(int(x)) for x in re.findall(r"[+-]\d+", s))


@dataclass
class ComparisonResult:
    rule: str
    verdict: str  # "improved" | "regressed" | "unchanged" | "new" | "removed"
    before_status: str | None
    after_status: str | None
    hours: int | None
    detail: str


def _entry_lines(entry: dict[str, Any]) -> int:
    return sum(parse_diff_stat(m.get("diff_stat")) for m in entry.get("modified", []))


def _compare_single(b: dict[str, Any], a: dict[str, Any]) -> str:
    b_err = b["status"] == "error"
    a_err = a["status"] == "error"
    if b_err and not a_err:
        return "improved"
    if not b_err and a_err:
        return "regressed"
    # Neither is error from here
    if b["status"] == "needs-work" and a["status"] == "success":
        return "improved"
    if b["status"] == "success" and a["status"] == "needs-work":
        return "regressed"
    if b["status"] == "needs-work" and a["status"] == "needs-work":
        b_lines = _entry_lines(b)
        a_lines = _entry_lines(a)
        if a_lines < b_lines:
            return "improved"
        if a_lines > b_lines:
            return "regressed"
    return "unchanged"


def _compare_rule_entries(
    before_entries: list[dict[str, Any]],
    after_entries: list[dict[str, Any]],
) -> tuple[str, str, str | None, str | None]:
    """Return (verdict, detail, before_status, after_status) for a rule."""
    before_by_project = {e["project_name"]: e for e in before_entries}
    after_by_project = {e["project_name"]: e for e in after_entries}

    all_projects = sorted(set(before_by_project) | set(after_by_project))
    verdicts = []
    for proj in all_projects:
        b = before_by_project.get(proj)
        a = after_by_project.get(proj)
        if b is None:
            verdicts.append("improved")
        elif a is None:
            verdicts.append("regressed")
        else:
            verdicts.append(_compare_single(b, a))

    if "regressed" in verdicts:
        roll_up = "regressed"
    elif "improved" in verdicts:
        roll_up = "improved"
    else:
        roll_up = "unchanged"

    # Build a representative detail string from the first project pair
    first_proj = all_projects[0] if all_projects else ""
    b0 = before_by_project.get(first_proj)
    a0 = after_by_project.get(first_proj)
    before_status = b0["status"] if b0 else None
    after_status = a0["status"] if a0 else None

    if before_status == "needs-work" and after_status == "needs-work":
        b_lines = _entry_lines(b0) if b0 else 0
        a_lines = _entry_lines(a0) if a0 else 0
        detail = f"needs-work ({b_lines} lines) -> needs-work ({a_lines} lines)"
    else:
        detail = f"{before_status} -> {after_status}"

    return roll_up, detail, before_status, after_status


def compare_results(before: dict[str, Any], after: dict[str, Any]) -> list[ComparisonResult]:
    """Compare two results dicts (from ick run --json) and return per-rule verdicts."""
    all_rules = sorted(set(before) | set(after))
    results = []

    for rule in all_rules:
        before_entries = before.get(rule)
        after_entries = after.get(rule)

        # Extract hours from whichever side has them
        hours: int | None = None
        for entries in (before_entries or [], after_entries or []):
            for entry in entries:
                if entry.get("hours") is not None:
                    hours = entry["hours"]
                    break
            if hours is not None:
                break

        if before_entries is None:
            after_status = after_entries[0]["status"] if after_entries else None
            results.append(
                ComparisonResult(
                    rule=rule,
                    verdict="new",
                    before_status=None,
                    after_status=after_status,
                    hours=hours,
                    detail=f"new rule (status: {after_status})",
                )
            )
        elif after_entries is None:
            before_status = before_entries[0]["status"] if before_entries else None
            results.append(
                ComparisonResult(
                    rule=rule,
                    verdict="removed",
                    before_status=before_status,
                    after_status=None,
                    hours=hours,
                    detail=f"rule removed (was: {before_status})",
                )
            )
        else:
            verdict, detail, before_status, after_status = _compare_rule_entries(before_entries, after_entries)
            results.append(
                ComparisonResult(
                    rule=rule,
                    verdict=verdict,
                    before_status=before_status,
                    after_status=after_status,
                    hours=hours,
                    detail=detail,
                )
            )

    return results


def summarize(comparisons: list[ComparisonResult]) -> dict[str, Any]:
    """Compute summary metrics: rules flagging counts and hours at risk."""
    _flagging = {"needs-work", "error"}

    def _is_flagging_before(c: ComparisonResult) -> bool:
        if c.verdict == "new":
            return False
        return c.before_status in _flagging

    def _is_flagging_after(c: ComparisonResult) -> bool:
        if c.verdict == "removed":
            return False
        return c.after_status in _flagging

    rules_before = sum(1 for c in comparisons if _is_flagging_before(c))
    rules_after = sum(1 for c in comparisons if _is_flagging_after(c))

    # Only sum hours when at least one rule has hours set
    has_hours = any(c.hours is not None for c in comparisons)
    if has_hours:
        hours_before: int | None = sum(c.hours or 0 for c in comparisons if _is_flagging_before(c))
        hours_after: int | None = sum(c.hours or 0 for c in comparisons if _is_flagging_after(c))
        hours_delta: int | None = hours_after - hours_before  # type: ignore[operator]
    else:
        hours_before = hours_after = hours_delta = None

    return {
        "rules_flagging_before": rules_before,
        "rules_flagging_after": rules_after,
        "rules_delta": rules_after - rules_before,
        "hours_before": hours_before,
        "hours_after": hours_after,
        "hours_delta": hours_delta,
    }


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    LOG.log(VLOG_1, "Run %s in %s", cmd, cwd or Path.cwd())
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd, check=True)
    if result.stdout:
        LOG.log(VLOG_2, "Stdout:\n%s", result.stdout)
    if result.stderr:
        LOG.log(VLOG_2, "Stderr:\n%s", result.stderr)
    return result


def run_ick_json(worktree_path: Path, target: Path, extra_args: list[str]) -> dict[str, Any]:
    """Run ick from a worktree against a target directory, returning the results dict."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(worktree_path)
    cmd = [sys.executable, "-m", "ick", "--target", str(target), "run", "--json"] + extra_args
    LOG.info("Running ick from %s against %s", worktree_path, target)
    result = _run(cmd, env=env)
    return json.loads(result.stdout)["results"]


@contextmanager
def managed_worktree(repo_root: Path, ref: str) -> Generator[Path, None, None]:
    """Create a temporary git worktree for the given ref, cleaning up on exit."""
    with TemporaryDirectory(prefix="ick-compare-") as td:
        wt_path = Path(td) / "wt"
        LOG.info("Creating worktree for %s at %s", ref, wt_path)
        _run(["git", "worktree", "add", "--detach", str(wt_path), ref], cwd=repo_root)
        try:
            yield wt_path
        finally:
            LOG.log(VLOG_1, "Removing worktree %s", wt_path)
            _run(["git", "worktree", "remove", "--force", str(wt_path)], cwd=repo_root)
