from ick._regex_translate import zfilename_re


def test_regex_matching_zfilenames() -> None:
    # start (and end)
    m = zfilename_re(["literal.txt"]).match("literal.txt\0")
    assert m.group("dirname") == ""  # type: ignore[union-attr] # FIX ME
    assert m.group("filename") == "literal.txt"  # type: ignore[union-attr] # FIX ME

    m = zfilename_re(["literal.txt"]).match("nope.txt\0")
    assert m is None

    m = zfilename_re(["literal.txt"]).match("foo/literal.txt\0")
    assert m.group("dirname") == "foo/"  # type: ignore[union-attr] # FIX ME
    assert m.group("filename") == "literal.txt"  # type: ignore[union-attr] # FIX ME

    # middle
    m = zfilename_re(["literal.txt"]).search("foo\0literal.txt\0foo\0")
    assert m.group("dirname") == ""  # type: ignore[union-attr] # FIX ME
    assert m.group("filename") == "literal.txt"  # type: ignore[union-attr] # FIX ME
