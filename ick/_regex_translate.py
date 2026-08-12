import re
from typing import Iterable


def rule_name_re(name: str, *, legacy: bool = False) -> str:
    """
    Return a regex used with ``fullmatch`` for rule selection.

    Both the new and legacy forms match a rule name plus descendants.
    The legacy form additionally converts a ``:`` prefix separator to ``/``.

    The ``:`` is kept so the result stays unambiguous when tried against both
    the prefixed and unprefixed name: a pattern containing one can only match a
    prefixed name, and a pattern without one can only match an unprefixed name.
    A trailing ``:`` therefore selects a whole ruleset without also picking up
    rules whose path merely starts with that prefix.
    """
    if legacy:
        return f"^{name.replace(':', '/').rstrip('/')}($|/.*$)"
    if name.endswith(":"):
        return f"^{name}.*$"
    return f"^{name.rstrip('/')}($|/.*$)"


def zfilename_re(opts: Iterable[str]) -> re.Pattern[str]:
    o = "|".join(map(re.escape, opts))
    # This regex could be made compatible with `re2` with a minor change of the
    # `(?=\0)` to `\b`.  This will match names like `pyproject.toml.template`
    # by mistake, and we'd need to check the next byte after the end to make
    # sure it's `\0` ourselves.
    s = f"(?:\\A|\\0)(?P<dirname>(?:[^\\0]*/)?)(?P<filename>{o})(?=\0)"
    return re.compile(s)
