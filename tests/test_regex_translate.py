from ick._regex_translate import zfilename_re


def test_regex_matching_zfilenames():
    # start (and end)
    m = zfilename_re(["literal.txt"]).match("literal.txt\0")
    assert m.group("dirname") == ""
    assert m.group("filename") == "literal.txt"

    m = zfilename_re(["literal.txt"]).match("nope.txt\0")
    assert m is None

    m = zfilename_re(["literal.txt"]).match("foo/literal.txt\0")
    assert m.group("dirname") == "foo/"
    assert m.group("filename") == "literal.txt"

    # middle
    m = zfilename_re(["literal.txt"]).search("foo\0literal.txt\0foo\0")
    assert m.group("dirname") == ""
    assert m.group("filename") == "literal.txt"
