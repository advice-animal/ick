import re


def advice_name_re(prefix: str) -> str:
    """
    returns a regular expression string that matches either prefix/ or prefix as the entire string.
    """
    return f"^({prefix}$|{prefix}/.*)$"


def zfilename_re(opts: list[str]) -> re.Pattern:
    o = "|".join(map(re.escape, opts))
    # This regex could be made compatible with `re2` with a minor change of the
    # `(?=\0)` to `\b`.  This will match names like `pyproject.toml.template`
    # by mistake, and we'd need to check the next byte after the end to make
    # sure it's `\0` ourselves.
    s = f"(?:\\A|\\0)(?P<dirname>(?:[^\\0]*/)?)(?P<filename>{o})(?=\0)"
    return re.compile(s)
