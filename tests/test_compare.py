from __future__ import annotations

import pytest

from ick.compare import ComparisonResult, compare_results, parse_diff_stat, summarize

# ---------------------------------------------------------------------------
# parse_diff_stat
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "s, expected",
    [
        (None, 0),
        ("", 0),
        ("+3", 3),
        ("-5", 5),
        ("+3-2", 5),
        ("+10-1", 11),
        ("+0", 0),
    ],
)
def test_parse_diff_stat(s: str | None, expected: int) -> None:
    assert parse_diff_stat(s) == expected


# ---------------------------------------------------------------------------
# Helpers for building fake results dicts
# ---------------------------------------------------------------------------


def _entry(
    status: str,
    *,
    project_name: str = "",
    diff_stat: str | None = None,
    hours: int | None = None,
) -> dict:
    mods = [{"file_name": "f.py", "diff_stat": diff_stat}] if diff_stat else []
    return {
        "project_name": project_name,
        "status": status,
        "modified": mods,
        "message": "",
        "metadata": None,
        "hours": hours,
    }


# ---------------------------------------------------------------------------
# compare_results: verdict transitions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "before_status, after_status, expected_verdict",
    [
        ("success", "success", "unchanged"),
        ("needs-work", "success", "improved"),
        ("success", "needs-work", "regressed"),
        ("error", "success", "improved"),
        ("error", "needs-work", "improved"),
        ("success", "error", "regressed"),
        ("needs-work", "error", "regressed"),
    ],
)
def test_verdict_status_transitions(before_status: str, after_status: str, expected_verdict: str) -> None:
    before = {"rule_a": [_entry(before_status)]}
    after = {"rule_a": [_entry(after_status)]}
    results = compare_results(before, after)
    assert len(results) == 1
    assert results[0].verdict == expected_verdict


def test_verdict_needs_work_fewer_lines_is_improved() -> None:
    before = {"rule_a": [_entry("needs-work", diff_stat="+10")]}
    after = {"rule_a": [_entry("needs-work", diff_stat="+3")]}
    results = compare_results(before, after)
    assert results[0].verdict == "improved"


def test_verdict_needs_work_more_lines_is_regressed() -> None:
    before = {"rule_a": [_entry("needs-work", diff_stat="+3")]}
    after = {"rule_a": [_entry("needs-work", diff_stat="+10")]}
    results = compare_results(before, after)
    assert results[0].verdict == "regressed"


def test_verdict_needs_work_same_lines_is_unchanged() -> None:
    before = {"rule_a": [_entry("needs-work", diff_stat="+5")]}
    after = {"rule_a": [_entry("needs-work", diff_stat="+5")]}
    results = compare_results(before, after)
    assert results[0].verdict == "unchanged"


def test_verdict_new_rule() -> None:
    before: dict = {}
    after = {"rule_a": [_entry("needs-work")]}
    results = compare_results(before, after)
    assert results[0].verdict == "new"
    assert results[0].before_status is None


def test_verdict_removed_rule() -> None:
    before = {"rule_a": [_entry("success")]}
    after: dict = {}
    results = compare_results(before, after)
    assert results[0].verdict == "removed"
    assert results[0].after_status is None


def test_hours_propagated_from_after() -> None:
    before = {"rule_a": [_entry("needs-work")]}
    after = {"rule_a": [_entry("success", hours=4)]}
    results = compare_results(before, after)
    assert results[0].hours == 4


def test_hours_propagated_from_before_when_absent_in_after() -> None:
    before = {"rule_a": [_entry("needs-work", hours=2)]}
    after = {"rule_a": [_entry("success", hours=None)]}
    results = compare_results(before, after)
    assert results[0].hours == 2


def test_multi_rule_ordering() -> None:
    before = {"z_rule": [_entry("needs-work")], "a_rule": [_entry("success")]}
    after = {"z_rule": [_entry("success")], "a_rule": [_entry("needs-work")]}
    results = compare_results(before, after)
    assert [r.rule for r in results] == ["a_rule", "z_rule"]
    assert results[0].verdict == "regressed"
    assert results[1].verdict == "improved"


def test_multi_project_any_regressed_wins() -> None:
    before = {
        "rule_a": [
            _entry("needs-work", project_name="proj1"),
            _entry("success", project_name="proj2"),
        ]
    }
    after = {
        "rule_a": [
            _entry("success", project_name="proj1"),
            _entry("needs-work", project_name="proj2"),
        ]
    }
    results = compare_results(before, after)
    assert results[0].verdict == "regressed"


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------


def _cr(verdict: str, before_status: str | None, after_status: str | None, hours: int | None = None) -> ComparisonResult:
    return ComparisonResult(
        rule="r",
        verdict=verdict,
        before_status=before_status,
        after_status=after_status,
        hours=hours,
        detail="",
    )


def test_summarize_empty() -> None:
    s = summarize([])
    assert s["rules_flagging_before"] == 0
    assert s["rules_flagging_after"] == 0
    assert s["rules_delta"] == 0
    assert s["hours_before"] is None
    assert s["hours_after"] is None
    assert s["hours_delta"] is None


def test_summarize_counts_flagging() -> None:
    comparisons = [
        _cr("improved", "needs-work", "success"),
        _cr("regressed", "success", "needs-work"),
        _cr("unchanged", "success", "success"),
        _cr("unchanged", "needs-work", "needs-work"),
    ]
    s = summarize(comparisons)
    assert s["rules_flagging_before"] == 2  # needs-work + needs-work
    assert s["rules_flagging_after"] == 2  # needs-work + needs-work
    assert s["rules_delta"] == 0


def test_summarize_new_and_removed() -> None:
    comparisons = [
        _cr("new", None, "needs-work"),
        _cr("removed", "needs-work", None),
    ]
    s = summarize(comparisons)
    assert s["rules_flagging_before"] == 1  # removed rule counted in before
    assert s["rules_flagging_after"] == 1  # new rule counted in after
    assert s["rules_delta"] == 0


def test_summarize_hours_delta() -> None:
    comparisons = [
        _cr("improved", "needs-work", "success", hours=4),
        _cr("regressed", "success", "needs-work", hours=2),
        _cr("unchanged", "needs-work", "needs-work", hours=3),
    ]
    s = summarize(comparisons)
    # before: needs-work (4h) + needs-work (3h) = 7h; after: needs-work (2h) + needs-work (3h) = 5h
    assert s["hours_before"] == 7
    assert s["hours_after"] == 5
    assert s["hours_delta"] == -2


def test_summarize_no_hours_when_all_none() -> None:
    comparisons = [
        _cr("regressed", "success", "needs-work", hours=None),
    ]
    s = summarize(comparisons)
    assert s["hours_before"] is None
    assert s["hours_after"] is None
    assert s["hours_delta"] is None


def test_summarize_partial_hours_treated_as_zero() -> None:
    comparisons = [
        _cr("regressed", "success", "needs-work", hours=None),
        _cr("unchanged", "needs-work", "needs-work", hours=5),
    ]
    s = summarize(comparisons)
    # has_hours=True because one entry has hours; the None entry contributes 0
    assert s["hours_before"] == 5
    assert s["hours_after"] == 5 + 0  # regressed: 0 before (was success), needs-work after but no hours
    assert s["hours_delta"] == 0
