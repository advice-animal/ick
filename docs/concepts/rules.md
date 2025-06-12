# Rules

A "rule" is something that ick runs to do one job.

Starting with one of the most minimal rules you could make, this one succeeds at
doing nothing:

```toml
[[rule]]
name = "pass"
impl = "shell"
scope = "project"
command = ":"
```

Among the configuration options you see there are `impl` (which is what
the rule is implemented in), and its `scope` (whether it runs on individual files,
projects, or repos).



## Scope

* `single-file` (the default) runs the rule assuming that it operates on
  individual files.  It's easy to run these concurrently.
* `project` runs the rule once per detected project -- you can additional
  restrict it to only run on certain types of projects as indicated by their
  [root markers](root_markers.md)
* `repo` runs the rule once per repo -- these can't parallelize well and should
  be used sparingly (for example, to operate only on files that other rules are
  unlikely to, like `.gitconfig`)

## By example


