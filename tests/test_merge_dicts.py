from ick.base_rule import GenericPreparedStep


def _make_step() -> GenericPreparedStep:
    """fake GenericPreparedStep for testing merge_dicts."""
    return object.__new__(GenericPreparedStep)


def test_none_returns_d2() -> None:
    step = _make_step()
    assert step.merge_dicts(None, {"findings": [1, 2]}) == {"findings": [1, 2]}


def test_empty_dict_returns_d2() -> None:
    step = _make_step()
    assert step.merge_dicts({}, {"findings": [1]}) == {"findings": [1]}


def test_lists_are_concatenated() -> None:
    step = _make_step()
    d1 = {"findings": [{"file": "a.py", "line": 1}]}
    d2 = {"findings": [{"file": "b.py", "line": 2}]}
    assert step.merge_dicts(d1, d2) == {"findings": [{"file": "a.py", "line": 1}, {"file": "b.py", "line": 2}]}


def test_new_keys_from_d2_added() -> None:
    step = _make_step()
    assert step.merge_dicts({"findings": [1]}, {"extra": "value"}) == {"findings": [1], "extra": "value"}


def test_nested_dicts_merged_recursively() -> None:
    step = _make_step()
    d1 = {"stats": {"errors": [1], "count": 5}}
    d2 = {"stats": {"errors": [2], "warnings": [3]}}
    assert step.merge_dicts(d1, d2) == {"stats": {"errors": [1, 2], "count": 5, "warnings": [3]}}


def test_scalar_values_overwritten_by_d2() -> None:
    step = _make_step()
    assert step.merge_dicts({"version": 1}, {"version": 2}) == {"version": 2}


def test_mutates_and_returns_d1() -> None:
    step = _make_step()
    d1 = {"findings": [1]}
    result = step.merge_dicts(d1, {"findings": [2]})
    assert result is d1


def test_multiple_merges_accumulate() -> None:
    """Simulates multiple batches merging into self.metadata."""
    step = _make_step()
    metadata = None
    metadata = step.merge_dicts(metadata, {"findings": [{"file": "a.py"}]})
    metadata = step.merge_dicts(metadata, {"findings": [{"file": "b.py"}]})
    metadata = step.merge_dicts(metadata, {"findings": [{"file": "c.py"}]})
    assert metadata == {"findings": [{"file": "a.py"}, {"file": "b.py"}, {"file": "c.py"}]}


def test_strings_concatenated_with_newline() -> None:
    step = _make_step()
    assert step.merge_dicts({"note": "batch1"}, {"note": "batch2"}) == {"note": "batch1\nbatch2"}


def test_strings_no_double_newline() -> None:
    step = _make_step()
    assert step.merge_dicts({"note": "batch1\n"}, {"note": "batch2"}) == {"note": "batch1\nbatch2"}
