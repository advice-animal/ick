def merge(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    elif isinstance(a, list):
        return a + b
    elif not a and isinstance(b, list):
        return b
    elif isinstance(a, dict):
        keys = a.keys() | b.keys()
        d = {}
        for k in keys:
            d[k] = merge(a.get(k), b.get(k))
        return d
    raise NotImplementedError()


def bucket(items, key):
    d = {}
    for i in items:
        k = key(i)
        d.setdefault(k, []).append(i)
    return d
