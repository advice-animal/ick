# Config

The full config is read and inherited from many locations, including

* `$XDG_CONFIG_DIR/advice-animal/ick/ick.toml`
* `$XDG_CONFIG_DIR/advice-animal/ick/ick.toml.local`
* `$REPO/ick.toml`
* `$REPO/pyproject.toml`

Any of these can define a `[[mount]]`, as detailed below.

Additionally, project-level configs are read for `do_not_want` and not much
else.

* `$PROJECT/ick.toml`
* `$PROJECT/pyproject.toml`


## Mounts

A mount is a reference to a dir or repo url that contains more `ick.toml` files
that define hooks or collections, and can contain arbitrary other files that we
want to exist on the filesystem (for example, compiled Go binaries).

The syntax with the doubled square brackets is called an [Array of
Tables](https://toml.io/en/v1.0.0#array-of-tables).

```toml
[[mount]]
url = "https://github.com/thatch/hobbyhorse"
prefix = "hh/"
```

(or in `pyproject.toml`)

```toml
[[tool.ick.mount]]
url = "https://github.com/thatch/hobbyhorse"
prefix = "hh/"
```

The `.local` one is in case the preceding one is provided by your employer, and
you want to add to it to flag more things with your own (personal) checks.

## Why just toml?

Because the repos I interact with already have a `pyproject.toml` which is a
place for putting multiple tools' config without cluttering the root with more
files.

If other languages have a similar concept, PRs welcome.
