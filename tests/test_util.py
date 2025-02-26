from ick.util import bucket, merge


def test_merge():
    assert merge(None, "x") == "x"
    assert merge("x", None) == "x"
    assert merge(["x"], ["y"]) == ["x", "y"]
    assert merge([], ["y"]) == ["y"]
    assert merge((), ["y"]) == ["y"]
    assert merge({"a": ["b"]}, {"a": ["c"]}) == {"a": ["b", "c"]}
    assert merge({"a": ["b"]}, {"b": ["c"]}) == {"a": ["b"], "b": ["c"]}


def test_bucket():
    rv = bucket([], key=lambda i: i == 2)
    assert rv == {}
    rv = bucket([1, 2, 3, 4], key=lambda i: i == 2)
    assert rv == {True: [2], False: [1, 3, 4]}
