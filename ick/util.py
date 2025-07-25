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
