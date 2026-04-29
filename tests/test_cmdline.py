from __future__ import annotations

from types import SimpleNamespace

from ick.cmdline import apply_filters
from ick.config import FilterConfig


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(obj=SimpleNamespace(filter_config=FilterConfig()))


def test_apply_filters_uses_new_matching_by_default() -> None:
    ctx = _ctx()
    apply_filters(ctx, ["subdir/rule"], "", allow_legacy_name_filter=False)

    assert ctx.obj.filter_config.allow_legacy_name_filter is False
    assert ctx.obj.filter_config.name_filter_re == "^subdir/rule($|/.*$)"
    assert ctx.obj.filter_config.legacy_name_filter_re == "^subdir/rule($|/.*$)"


def test_apply_filters_can_force_legacy_matching() -> None:
    ctx = _ctx()
    apply_filters(ctx, ["rule/subdir/rule"], "", allow_legacy_name_filter=True)

    assert ctx.obj.filter_config.allow_legacy_name_filter is True
    assert ctx.obj.filter_config.name_filter_re == "^rule/subdir/rule($|/.*$)"
    assert ctx.obj.filter_config.legacy_name_filter_re == "^rule/subdir/rule($|/.*$)"


def test_apply_filters_does_not_fallback_for_substring_search() -> None:
    ctx = _ctx()
    apply_filters(ctx, [], "needle", allow_legacy_name_filter=False)

    assert ctx.obj.filter_config.allow_legacy_name_filter is False
    assert ctx.obj.filter_config.name_filter_re == ".*needle.*"
    assert ctx.obj.filter_config.legacy_name_filter_re == ".*needle.*"
