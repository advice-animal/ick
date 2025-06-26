from ick.util import bucket, merge


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
