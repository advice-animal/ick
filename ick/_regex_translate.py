import re
from typing import Iterable


def rule_name_re(name: str, *, legacy: bool = False) -> str:
    """
    Return a regex used with ``fullmatch`` for rule selection.

    Rule name filters are a hybrid of path-style prefix matching and raw regex.
    The ``name`` argument is embedded as-is (no ``re.escape``): callers are
    responsible for escaping any metacharacters in literal names they pass in.
    The ``($|/.*$)`` suffix anchors the match to a name *or* any descendant
    path (e.g. ``python`` matches ``python/isort`` and ``python/black``).

    The legacy form additionally rewrites a ``:`` prefix separator to ``/`` so
    that the old ``repo/path`` naming style still matches.
    """
    if legacy:
        return f"^{name.replace(':', '/').rstrip('/')}($|/.*$)"
    return f"^{name.rstrip('/')}($|/.*$)"


def zfilename_re(opts: Iterable[str]) -> re.Pattern[str]:
    o = "|".join(map(re.escape, opts))
    # This regex could be made compatible with `re2` with a minor change of the
    # `(?=\0)` to `\b`.  This will match names like `pyproject.toml.template`
    # by mistake, and we'd need to check the next byte after the end to make
    # sure it's `\0` ourselves.
    s = f"(?:\\A|\\0)(?P<dirname>(?:[^\\0]*/)?)(?P<filename>{o})(?=\0)"
    return re.compile(s)
