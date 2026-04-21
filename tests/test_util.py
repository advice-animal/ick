from pathlib import Path

import pytest

from ick.util import bucket, convert_path_to_python_identifiers, merge


def test_merge() -> None:
    assert merge(None, "x") == "x"  # type: ignore[no-untyped-call] # FIX ME
    assert merge("x", None) == "x"  # type: ignore[no-untyped-call] # FIX ME
    assert merge(["x"], ["y"]) == ["x", "y"]  # type: ignore[no-untyped-call] # FIX ME
    assert merge([], ["y"]) == ["y"]  # type: ignore[no-untyped-call] # FIX ME
    assert merge((), ["y"]) == ["y"]  # type: ignore[no-untyped-call] # FIX ME
    assert merge({"a": ["b"]}, {"a": ["c"]}) == {"a": ["b", "c"]}  # type: ignore[no-untyped-call] # FIX ME
    assert merge({"a": ["b"]}, {"b": ["c"]}) == {"a": ["b"], "b": ["c"]}  # type: ignore[no-untyped-call] # FIX ME


def test_bucket() -> None:
    rv = bucket([], key=lambda i: i == 2)  # type: ignore[no-untyped-call] # FIX ME
    assert rv == {}
    rv = bucket([1, 2, 3, 4], key=lambda i: i == 2)  # type: ignore[no-untyped-call] # FIX ME
    assert rv == {True: [2], False: [1, 3, 4]}


@pytest.mark.parametrize(
    "path, expected",
    [
        ("./new-dir", "./new_dir"),
        ("nochange", "nochange"),
        ("many-many/dirs-are-in/this-path/but-no-python-files", "many_many/dirs_are_in/this_path/but_no_python_files"),
        ("what----a-weird-dirname", "what____a_weird_dirname"),
        (".", "."),
    ],
)
def test_convert_path_to_python_identifiers(path: str, expected: str) -> None:
    assert convert_path_to_python_identifiers(Path(path)) == Path(expected)
