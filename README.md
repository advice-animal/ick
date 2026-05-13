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




<!--

## Don't Reinvent the Wheel

This is going to sound a little like a "what we are not" section, but in short,
the goal is to be able to compose existing tools to produce a greater whole.

* This isn't designed to run in your IDE.
* This isn't designed for every rule to mutate every file every time.
* This isn't designed for a multi-gigabyte repo.
* This isn't designed to run on a Pi 1.

It *is* designed to automate the kind of things that people either put in shell
scripts, or don't write because the one-off effort of making a shell script
doesn't seem rewarding, and provide a way for language-agnostic discovery.

## More Details

Each rule runs in parallel.  Best case, this means you get to use all your
cores and get a fully passing score.  We all want that.  But if your code has
some fixes that we think you'd want, then subsequent rules get re-run.

I know what you're thinking, *CS Student*, "but isn't that `O(n**2)`?"  Yes,
but with just a tiny bit of optimism (things aren't always going to change)
it's much more like `k * O(n)`.


**In More Detail**




really out of date could probably use starting over from modern templates.

You *could* chain together a bunch of shell scripts to modernize things using
appropriate tools.  But if this is the sort of thing you do at scale and want
to distribute recommendations that people can adopt as they have time, you need
automation.


Its primary job is to let you *move towards a goal over time* and make it
*trivially easy to write fixes with good tests*.  You can adopt ick without
your entire team having to commit to it, and you can walk away if it doesn't do
what you want.


*The Elevator Pitch*

When you set up your project, you probably use the latest recommendations when
doing so.  For example, using the latest version of a pre-commit hook, the
latest version of GH `actions/upload`, and a `ruff` config you copy-pasted from
somewhere.

We (as developers) pin these so that a single commit of *our* project should
pass or fail consistently, and we have the choice of when to update.  But what
provides the advice that those recommendations have changed, to get us to
update?

``ick`` is all about still leaving choice in the hands of repo owners, while also
being able to subscribe to the advice of people with good opinions -- whether
that's a central team at your job, or you personally trying to keep a dozen open
source repos in sync.  We want things to converge... eventually.

It also has the explicit goal of being able to scale from low-risk, easy changes
(*"text files should end with a newline"*) to medium changes (*"you should drop
python 3.6 support and sync your github actions matrix"*) to large ones (*"here's
the beginning of a refactor to enable testcontainers"*) or even ones that
involve external state.  The effort to write the advice should be roughly
proportional to how complex it is -- easy things should be easy (and fast!), but
it's ok for hard things to still be hard.

## Where can it run?

* Developers can run it directly
* You could send out sourcegraph-style batch changes
* Managers can see the results if you store the reports in a db
* TODO: Someone could make a bot that creates PRs and/or Issues

The one place it's not intended to run is CI on every commit.  There are
existing tools that satisfy that space (for example, `pre-commit` and `ruff`
directly).


## Multi-project support

Some repositories contain multiple projects, for example a Java project and a
Python client and Go CLI.  `Ick` lets you (well, the central-team "you")
customize the markers that indicate a project root, separate from the repo
root.


## Low-config parallel linting

`Ick` is optimistic that recommendations won't conflict.  Unless you configure
otherwise, it's assumed that the only input a hook needs is the file
it's being asked to check.  While this is true for simple operations like code
formatters, maybe a recommendation is to move something from one file to
another, and that invalidates another recommendation if applied first.

`Ick` runs them both, determines which is ordered first, applies that, and
invalidates (re-runs) the recommendation job where a result was based on a
now-stale input.

TODO: Benchmarks after more real-world use -- as long as formatting comes last,
we shouldn't have a ton of re-runs.


## Multi-language recommendation jobs

One way this is like (and based on) `pre-commit` is that you can run anything
from a shell oneliner up to a full docker image, and several things in between
(such as a Python project with dependencies that builds a venv when changed).

-->
