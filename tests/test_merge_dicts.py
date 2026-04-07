from ick.util import merge_dicts


def test_none_returns_d2() -> None:
    assert merge_dicts(None, {"findings": [1, 2]}) == {"findings": [1, 2]}


def test_empty_dict_returns_d2() -> None:
    assert merge_dicts({}, {"findings": [1]}) == {"findings": [1]}


def test_lists_are_concatenated() -> None:
    d1 = {"findings": [{"file": "a.py", "line": 1}]}
    d2 = {"findings": [{"file": "b.py", "line": 2}]}
    assert merge_dicts(d1, d2) == {"findings": [{"file": "a.py", "line": 1}, {"file": "b.py", "line": 2}]}


def test_new_keys_from_d2_added() -> None:
    assert merge_dicts({"findings": [1]}, {"extra": "value"}) == {"findings": [1], "extra": "value"}


def test_nested_dicts_merged_recursively() -> None:
    d1 = {"stats": {"errors": [1], "count": 5}}
    d2 = {"stats": {"errors": [2], "warnings": [3]}}
    assert merge_dicts(d1, d2) == {"stats": {"errors": [1, 2], "count": 5, "warnings": [3]}}


def test_scalar_values_overwritten_by_d2() -> None:
    assert merge_dicts({"version": 1}, {"version": 2}) == {"version": 2}


def test_mutates_and_returns_d1() -> None:
    d1 = {"findings": [1]}
    result = merge_dicts(d1, {"findings": [2]})
    assert result is d1


def test_multiple_merges_accumulate() -> None:
    """Simulates multiple batches merging into self.metadata."""
    metadata = None
    metadata = merge_dicts(metadata, {"findings": [{"file": "a.py"}]})
    metadata = merge_dicts(metadata, {"findings": [{"file": "b.py"}]})
    metadata = merge_dicts(metadata, {"findings": [{"file": "c.py"}]})
    assert metadata == {"findings": [{"file": "a.py"}, {"file": "b.py"}, {"file": "c.py"}]}


def test_strings_concatenated_with_newline() -> None:
    assert merge_dicts({"note": "batch1"}, {"note": "batch2"}) == {"note": "batch1\nbatch2"}


def test_strings_no_double_newline() -> None:
    assert merge_dicts({"note": "batch1\n"}, {"note": "batch2"}) == {"note": "batch1\nbatch2"}
