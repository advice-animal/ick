There are many existing tools that (if you know about them) can improve your
code.  One in particular is `pre-commit` which is intended to be run and provide
a stable result on a commit.

We actually drew a lot of inspiration (and some obscure `git` args) from
`pre-commit`, but with near opposite goals: as opinions change over time, the
recommendations for your code should too.

"Whose opinions?" is a good question.  And not one that `ick` really answers for
you, after all, it starts off with a blank slate with no recommendations.  This
is primarily intended for people managing multiple repos, whether it's because
they are prolific at creating new projects (guilty!) or are at a company with a
central platform team that wants to provide recommendations of increasing
"encouragement" to accept them.

The recommendations don't need to come with autofixes, but they certainly can.
Where possible, `ick` tries to not leave you in a non-working repo state (e.g.
fixes that exit 1 get rolled back).
