# Rules

A rule is something that ick runs to do one job.  They are implemented as
standalone programs and described by metadata in an ick.toml file.

Starting with one of the most minimal rules you could make, this one succeeds at
doing nothing:

```toml
[[rule]]
name = "do_nothing"
impl = "shell"
scope = "project"
command = ":"
```

Among the configuration options you see there are `impl` (which is what
the rule is implemented in), and its `scope` (whether it runs on individual files,
projects, or repos).

## Impls

Ick supports a number of choices for rule implementation and can be extended to
support more.  Currently we support Python and shell.  See [Implementation
engines](../reference/impls.html) for details.


## Scope

A rule's scope determines how it is invoked in a repo.

* `file` (the default) runs the rule on individual files matching a pattern
    supplied with the rule.
* `project` runs the rule once per detected project in the repo.
* `repo` runs the rule once per repo.

See [Scopes](scope.html) for more details.


## Urgency

Unlike other compliance tools that describe issues as "error" vs "warning" or
other levels, ick uses the more human-focused, actionable "urgency."

While people can choose to run rules in any order, this allows grouping and
inferences of their priorities.

For example, a pending deprecation in 3 months might be `"now"` and once it's
actually deprecated might be `"urgent"`.
