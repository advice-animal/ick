from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import click

from ick.cmdline import _flatten_tags, apply_filters
from ick.config import FilterConfig


def _ctx() -> click.Context:
    return cast(click.Context, SimpleNamespace(obj=SimpleNamespace(filter_config=FilterConfig())))


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


def test_apply_filters_sets_tags() -> None:
    ctx = _ctx()
    apply_filters(ctx, [], "", tags=["security", "python"])

    assert ctx.obj.filter_config.tags == ["security", "python"]


def test_apply_filters_combines_tags_with_positional_filters() -> None:
    ctx = _ctx()
    apply_filters(ctx, ["some_rule"], "", tags=["security"])

    assert ctx.obj.filter_config.tags == ["security"]
    assert ctx.obj.filter_config.name_filter_re == "^some_rule($|/.*$)"


def test_apply_filters_combines_tags_with_substring() -> None:
    ctx = _ctx()
    apply_filters(ctx, [], "needle", tags=["security"])

    assert ctx.obj.filter_config.tags == ["security"]
    assert ctx.obj.filter_config.name_filter_re == ".*needle.*"


def test_flatten_tags_splits_commas_and_dedupes_flags() -> None:
    assert _flatten_tags(["security,python", "lint"]) == ["security", "python", "lint"]


def test_flatten_tags_empty() -> None:
    assert _flatten_tags(()) == []
