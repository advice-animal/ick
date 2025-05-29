# Config

The full config is read and inherited from many locations, including

<!--
TODO: On Mac, XDG_CONFIG_DIR is ignored, but also, the path seems different
than the appdirs code?  The appdirs code looks like it will go to
`~/Library/Preferences`, but it's actually `~/Library/Application Support`,
which is appdirs.user_data_dir.
-->

* `$XDG_CONFIG_DIR/ick/ick.toml`
* `$XDG_CONFIG_DIR/ick/ick.toml.local`
* `$REPO/ick.toml`
* `$REPO/pyproject.toml`

Any of these can define one or more `[[ruleset]]` sections, as detailed below.

Additionally, project-level configs are read for `do_not_want` and not much
else.

* `$PROJECT/ick.toml`
* `$PROJECT/pyproject.toml`


## Rulesets

A ruleset is a directory or repo url that contains more `ick.toml` files
that define hooks and can contain arbitrary other files that we
want to exist on the filesystem (for example, compiled Go binaries).

The syntax with the doubled square brackets is called an [Array of
Tables](https://toml.io/en/v1.0.0#array-of-tables).

```toml
[[ruleset]]
url = "https://github.com/thatch/hobbyhorse"
prefix = "hh/"
```

(or in `pyproject.toml`)

```toml
[[tool.ick.ruleset]]
url = "https://github.com/thatch/hobbyhorse"
prefix = "hh/"
```

The `.local` one is in case the preceding one is provided by your employer, and
you want to add to it to flag more things with your own (personal) checks.

## Why just TOML?

Because the repos I interact with already have a `pyproject.toml` which is a
place for putting multiple tools' config without cluttering the root with more
files.

If other languages have a similar concept, PRs welcome.
