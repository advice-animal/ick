import re
from typing import Iterable


def rule_name_re(prefix: str) -> str:
    """
    Returns a regular expression string that matches either prefix/ or prefix
    as the entire string.  The regex is used with re.fullmatch.
    """
    return f"^{prefix}($|/.*$)"


def zfilename_re(opts: Iterable[str]) -> re.Pattern[str]:
    o = "|".join(map(re.escape, opts))
    # This regex could be made compatible with `re2` with a minor change of the
    # `(?=\0)` to `\b`.  This will match names like `pyproject.toml.template`
    # by mistake, and we'd need to check the next byte after the end to make
    # sure it's `\0` ourselves.
    s = f"(?:\\A|\\0)(?P<dirname>(?:[^\\0]*/)?)(?P<filename>{o})(?=\0)"
    return re.compile(s)
