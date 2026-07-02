# Ick

<img align="right" src="https://raw.githubusercontent.com/advice-animal/ick/main/_static/ick.png" width="200" height="191">

Ick is a polyglot tool for bundling best practices as versioned, runnable rules
and checking any number of repos against them — with or without auto-fixes.

Full documentation at https://ick.readthedocs.io.

## The problem

Best practices don't live in one place.  They're scattered across:

* pre-commit hooks that have to be wired up in every repo individually
* CI workflows that also have to be added to every repo individually
* central automation (secrets scanners, security audits) that runs on your
  infrastructure but whose results developers can't easily reproduce locally
* wiki pages and style guides that developers have to remember to consult
* one-off shell scripts that only the author runs

Ick isn't trying to replace any of those things.  It's a single locus for
storing those checks and fixes as well as ones that don't fit neatly into any
of those boxes.  It still respects distributed principles: rules are versioned
in a repo, developers can run them locally on their own machines, and no single
repo has to opt in for you to get started.

> [!TIP]
> **Concrete example:** You want to run [zizmor](https://github.com/woodruffw/zizmor)
> on every repo that has GitHub Actions workflows.  Your options today are to
> add it as a pre-commit hook in every repo, add it as a workflow in every
> repo, or remember to run it yourself.  With ick, you write one rule in a
> central rules repo and run it against any repo you want.  No per-repo
> configuration required.  And when the next security scanner comes along, you
> update the rule once.

When something looks wrong, developers can run ick locally to reproduce the
result and debug what the rule is seeing — no waiting for CI, no digging through
logs on a remote system.

When a best practice evolves — say, a new scanner ships, or a deprecated API
needs to be removed — you can answer *"which of my repos are already compliant,
and which ones still need work?"*

The traditional dev loop looks like this:

```
    /----------------\  push  /----------------\
    |  code          |------->|  integrate     |
    |      build     |        |     test       |
    |          test  |        |        deploy  |
    \----------------/        \----------------/

       inner loop                 outer loop
```

but that discounts the big-picture software maintenance stuff that healthy
projects ought to do, and commonly forget (or accomplish with one-off scripts)
on a longer term basis.  For that we really ought to keep track of things
that aren't "right now" and aren't "today" but are "important, yet not urgent".

```
    /----------------\  push  /----------------\  stable  /==================\
    |  code          |------->|  integrate     |--------->| tech debt week   |
    |      build     |        |     test       |          |  quantified proj |
    |          test  |        |        deploy  |          |   bootcamp tasks |
    \----------------/        \----------------/          |    deprecations  |
                                                          \==================/
       inner loop                 outer loop                 planning cycle
```

Ick manages and runs rules to help you keep track of that third loop across
as many repos as you need.


## Elevator pitch

`ick` looks at your source code and gives you an evaluation against a set of
rules.  Those rules might come from a central team at your work, or a trusted
friend, or they might be ones you maintain yourself (like my hobbyhorse, "text
files must end with a newline").

Rules don't have to fix anything.  A rule that just *checks* — and exits with a
status code to signal "needs work" — is a first-class citizen.  You can add the
auto-fix later, or never.  Checks can be written in any language and can target
any language: a shell one-liner, a Python script, a Go binary, a Docker image —
whatever tool fits the job.

If you're ever tempted to make a one-off shell script, or create a
`scripts/release-check.sh` that you run once in a while, then ick is the loose
automation framework you're looking for. Ick makes that kind of work easier to
scale past a couple of repos.

Rules run in parallel by default.  For a repo with many rules, ick fans them
all out at once, re-running only the rules whose inputs changed.  This is
uncommon in tools of this kind and matters a lot when your ruleset grows.

Ick also has the explicit goal of being able to scale from low-risk, easy
changes (*"text files should end with a newline"*) to medium changes (*"you
should drop Python 3.6 support and sync your GitHub Actions matrix"*) to large
ones (*"here's the beginning of a refactor to enable testcontainers"*) or even
ones that involve external state.  The effort to write rules should be roughly
proportional to how complex they are -- easy things should be easy (and fast!),
but it's OK for hard things to still be hard.


## Who is ick for?

* **Central teams** with opinions. For example, at a company, there might be a
  security team, a language team, or a platform team — and they all might want
  to publish rules that say "here's what compliant looks like" without having
  to touch every repo themselves.
* **Projects** with opinions. Say your ML project has decided to only bless a
  certain model or license.
* **Developers** with multiple repositories they want to keep looking similar.
* **Developers** with [hobby horses](https://wiki.c2.com/?HobbyHorse), who are
  stricter about things others don't (yet) care about.


## Changelog

### Unreleased

- Rules can now have `tags` (a list of strings). Filter rules by tag with
  `-t`/`--tag` on `run`, `test-rules`, and `list-rules`, for example
  `ick run -t security` or `ick run -t security,python`.

### v0.11.0 (June 9, 2026)

- File name patterns in `inputs=` settings now match more intuitively. If the
  pattern has no slash, it will match anywhere in the project. With a slash,
  the pattern must match the full relative path from the root of the project.
  Previously, a pattern with no slash would match anywhere if it started with a
  wildcard star (such as `*.py`), but without the wildcard, only a file in the
  root of the project would match.
