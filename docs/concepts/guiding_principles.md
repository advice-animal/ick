# Guiding Principles

First, the pithy version:

* First, corrupt no source code.
* Second, don't reinvent what works.

## Explicit Goals

* Always give you an "undo" (default to an informative dry run)
* Be something that one person on a team can adopt, if they're the only one that cares
* Be something that you can run infrequently (say, before a release or in a tech
  debt week), while resepcting the amount of time you have available
* Don't be tied to any one {language,os,etc}: Be agnostic to what tools people
  want to use
* Give you a heads-up about recommendations that you don't need to apply yet
  (but can if you have spare time or want to be an early adopter)

By focusing on a sliding scale of effort, we can apply automation where it
makes sense, especially on the low end of complexity.  If you haven't wanted to
write a custom flake8 plugin because it's hard, and resorted to a `grep`
somewhere, this framework is for you.

## On-Ramps

To make it easier to try or, or for only certain people to use at the
beginning, it must be possible to use `ick` in an existing repo with the most
minimal configuration possible.

You should also be able to script `ick`, running it on directories and doing
your own operations on the output.  `Ick` won't be creating you PRs using the
GitHub API, but you should be able to build such an automation for yourself or
your company.

You should be able to run `ick` with point-in-time rules from something like a
Sourcegraph Batch Change, which means it should be easy to package into a
Docker image with your own custom rules.

## Off-Ramps

You should be able to stop using `ick` with only things users have explicitly
done (like suppressions or ignores) left behind.
