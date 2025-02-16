# Collections

A *collection* is basically a set of *hook* that runs at the same
`order`, and shares a single environment (for Python, that means the same
virtualenv and dependencies).

They can also come up with their hook names dynamically, for example based on
another config file.

You define them in much the same way as [hooks](hooks.md):

```toml
[[collection]]

language = "python"
```

If there are `<dir>/__init__.py` files in under the current directory, this
expands to hooks with names inferred from `<dir>`.  Otherwise it's just an empty
collection.

If you'd rather keep the collection's files in a subdir (for example, because
you have multiple collections defined in the same config), just specify `subdir=`
