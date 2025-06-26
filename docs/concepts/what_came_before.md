# What came before

Ick is not the first tool to examine and modify source code -- these have
existed since the beginning of (unix)time, and there are several successful
ones that we drew inspiration from (and either still use ourselves for other
uses, or use _within_ an `ick` rule).

All of the tools mentioned here are good at something. `ick` is good at
orchestration and tries to leave you to your own devices.  See if you agree with
[Guiding Principles](guiding_principles.html) and [Norms](norms.html) for the
remaining limitations that might be worth writing an even better tool.


## Multi-file, multi-language

  * pre-commit: https://github.com/pre-commit/pre-commit/

    Firstly, `pre-commit` is the only truly polyglot tool in this list that works
    without tons of configuration.

    We actually drew a lot of inspiration (and some obscure `git` args) from
    `pre-commit`, but with near opposite goals: as opinions change over time, the
    recommendations for your code should too.  `pre-commit` is intended for
    rules that are fully specified by your source code.

    This difference is mostly down to whether you want to run it in CI.
    `pre-commit` says "sure!" and `ick` says "please don't."

  * arc lint: https://secure.phabricator.com/book/phabricator/article/arcanist\_lint/

    The inspiration for running rules in parallel (although it ships back only
    diffs, limiting it to text files), this requires buy-in from a project before
    you can reasonably run it, and also requires configuration (e.g. regex for
    finding line numbers from error messages) and how you get your lint binaries to
    people.  We store all that in (any number of) rule repos.

## Multi-language DSL

  * semgrep: https://github.com/semgrep/semgrep
  * ast-grep: https://ast-grep.github.io/

    The best polyglot solutions (based on tree-sitter), and quite fast, but not
    powerful enough (at least for Python), and without a great off-ramp except for
    using them as libraries (which you can do under ick).

  * openrewrite

    Java-focused, although it supports other languages; doesn't provide a way
    to start simple.  Takes a central view of where rules go (and basically
    needs to run in docker).

## Python only

  * libcst.codemod: https://libcst.readthedocs.io/en/latest/codemods.html
  * fixit: https://fixit.readthedocs.io/en/stable/

    Tim was tangentially involved in the development of these, and the way
    rules are defined and tested in a much more generic way is intentionally
    the polar opposite.

    Several good libraries were written for these, including `trailrunner` that
    you might use in other circumstances.

  * bowler: https://pybowler.io/

    Not under active development anymore, this was a good option for a long
    time, but like all lib2to3-based projects can't support modern Python syntax.

    One good concept that came from this is how function signatures get parsed,
    which handles positional and keyword arguments.  I wish more tools did that.
