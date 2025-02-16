# Ick

<img align="right" src="_static/ick.png" width="300" height="287">
In a nutshell, ick can tell you what best practices you haven't adopted, and
in many cases[citation needed] fix them for you.  It's not tied to any one use
case or CI/CD platform, and is completely free to use, improve (MIT license),
and customize (it comes with no inbuilt opinions, but makes it easy to add your
own or others').

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


## Explicit Goals

* First, do no harm (always give you an "undo", default to an informative dry run)
* Be something that one person on a team can adopt, if they're the only one that cares
* Be something that you can run infrequently (say, before a release or in a tech
  debt week), while resepcting the amount of time you have available
* Don't be tied to any one {language,os,etc}: Be agnostic to what tools people
  want to use
* Give you a heads-up about recommendations that you don't need to apply yet
  (but can if you have spare time or want to be an early adopter)
