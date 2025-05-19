from collections.abc import Sequence


def merge(a, b):
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
            d[k] = merge(a.get(k), b.get(k))
        return d
    raise NotImplementedError(f"Can't merge {type(a)} with {type(b)} having values {a} and {b}")


def bucket(items, key):
    d = {}
    for i in items:
        k = key(i)
        d.setdefault(k, []).append(i)
    return d
