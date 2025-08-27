import re

from ick._regex_translate import rule_name_re, zfilename_re


def test_advice_name_matching() -> None:
    foo_match = re.compile(rule_name_re("foo")).fullmatch
    assert foo_match("foo")
    assert foo_match("foo/hello")
    assert foo_match("foo/hello/goo")
    assert not foo_match("food_truck")
    assert not foo_match("py/foo")
    assert not foo_match("py/foo/goo")


def test_regex_matching_zfilenames() -> None:
    # start (and end)
    m = zfilename_re(["literal.txt"]).match("literal.txt\0")
    assert m is not None
    assert m.group("dirname") == ""
    assert m.group("filename") == "literal.txt"

    m = zfilename_re(["literal.txt"]).match("nope.txt\0")
    assert m is None

    m = zfilename_re(["literal.txt"]).match("foo/literal.txt\0")
    assert m is not None
    assert m.group("dirname") == "foo/"
    assert m.group("filename") == "literal.txt"

    # middle
    m = zfilename_re(["literal.txt"]).search("foo\0literal.txt\0foo\0")
    assert m is not None
    assert m.group("dirname") == ""
    assert m.group("filename") == "literal.txt"
