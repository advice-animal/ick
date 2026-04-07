from collections.abc import Sequence


def merge(a, b):  # type: ignore[no-untyped-def] # FIX ME
    if a is None:
        return b
    elif b is None:
        return a
    elif isinstance(a, Sequence):
        return [*a, *b]
    elif not a and isinstance(b, Sequence):
        return b
    elif isinstance(a, dict):
        keys = a.keys() | b.keys()
        d = {}
        for k in keys:
            d[k] = merge(a.get(k), b.get(k))  # type: ignore[no-untyped-call] # FIX ME
        return d
    raise NotImplementedError(f"Can't merge {type(a)} with {type(b)} having values {a} and {b}")


def bucket(items, key):  # type: ignore[no-untyped-def] # FIX ME
    d = {}  # type: ignore[var-annotated] # FIX ME
    for i in items:
        k = key(i)
        d.setdefault(k, []).append(i)
    return d


def merge_dicts(d1: dict | None, d2: dict | None) -> dict | None:
    if not d1:
        return d2

    elif not d2:
        return d1

    else:
        for k in d1:
            if k in d2:
                if isinstance(d2[k], dict):
                    # we technically should check if d1[k] is also a but since both jsons are created by the same script it's fine
                    d1[k] = merge_dicts(d1[k], d2[k])

                elif isinstance(d2[k], list):
                    d1[k] += d2[k]

                elif isinstance(d2[k], str) and isinstance(d1[k], str):
                    # concat messages as best as we can
                    if not d1[k].endswith("\n"):
                        d1[k] += "\n"

                    d1[k] += d2[k]

                else:
                    # this is hard. Override one of the values and then recommend in docs that rule writers only use lists and dicts.
                    d1[k] = d2[k]

        for k in d2:
            if k not in d1:
                d1[k] = d2[k]

        return d1


def diffstat(diff_text: str) -> str:
    # A typical diff stars with the lines
    #
    # --- a
    # +++ b
    #
    # Only the + line needs to subtract one; this approximate.
    added = diff_text.count("\n+") - 1
    removed = diff_text.count("\n-")
    s = ""
    if added:
        s += f"+{added}"
    if removed:
        s += f"-{removed}"
    return s
