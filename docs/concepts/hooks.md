# Hooks

Borrowing the terminology from `pre-commit`, a "hook" is something that this
tool runs to do one job.

Starting with one of the most minimal hooks you could make, this one succeeds at
doing nothing:

```toml
[[hook]]
name = "pass"
language = "shell"
scope="project"
command = ":"
```

Among the configuration options you see there are the `language` (which is what
the hook is written in), and its `scope` (whether it runs on individual files,
projects, or repos).



## Scope

* `single-file` (the default) runs the hook assuming that it operates on
  individual files.  It's easy to run these concurrently.
* `project` runs the hook once per detected project -- you can additional
  restrict it to only run on certain types of projects as indicated by their
  [root markers](root_markers.md)
* `repo` runs the hook once per repo -- these can't parallelize well and should
  be used sparingly (for example, to operate only on files that other hooks are
  unlikely to, like `.gitconfig`)

## By example


