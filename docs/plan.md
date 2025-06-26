# repo/set-license

# repo/update-gitignore

# repo/mailmap

# repo/code-of-conduct

# repo/readme-shouldnt-say-fixme

# python/project-definition/stop-using-poetry

# python/project-definition/use-lockfiles

# python/project-definition/your-lockfile-is-invalid

Depends on `troch` or `pkg_resources` in .in, or chosen version in .txt yanked.

# python/project-definition/your-lockfile-can-be-updated

# python/project-definition/setuptools-explicit-packages-skipped-some

If you're not using `find_packages()` or `find:` and some subpackages aren't
included in the list.  Example of something you might want to turn off
per-project, and something that's difficult to put a line-based suppression on.

# python/project-definition/setuptools-declarative-config

Maybe to setup.cfg, maybe full pep 517

# python/project-definition/use-canonical-name
# python/project-definition/use-canonical-version

# python/deps/dwyu

Depend on what you use (all direct imports should be in your direct deps)

Would be great if this didn't require a live virtualenv.

# python/deps/canonical-names

# python/deps/include-upper-bound

# python/deps/dont-pin-in-public-deps

# python/decorators/async-test-should-cone-first

Orders test decorators if you use unittest, I guess.  Might be something you
modify from upstream, or put names in config, and need multi-file fqn.

Multi-file fqn might need config overrides too.

# python/decorators/wrapper

Ensures functools.wraps if you take a func and return something that calls it


# python/lint/ruff-should-isort
# python/lint/use-ruff

Make sure to reformat, add suppressions

# python/lint/update-ruff

Make sure to reformat, add suppressions


# python/types/include-py-typed

(plus maybe `include_package_data`)

# python/types/adopt-mypy

Enable type checking using mypy.  Runs custom mypy-upgrade after.

# python/types/upgrade-mypy

Runs after adopt, when version needs to change.  Runs custom mypy-upgrade after.

# python/types/install-types-needs-uv-seed

# python/types/need-dfferent-generic-params

Use of the wrong number of parameters, e.g. use of Dict or Dict[foo] not Dict[foo, bar]

# python/types/string-annotations

1. If you use string annotations, don't.
2. If you're compatible with 3.7 or 3.8 also include the future annotations
3. Use lowercase list, dict, etc and remove the imports if no references are
   left (e.g. in assignments, not type hints)

https://peps.python.org/pep-0563/ (deferred evaluation)
https://peps.python.org/pep-0585/ (lowercase generics)

# python/types/stubs-should-include-public-names

# python/migration/runtime

# python/migration/psycopg2

# python/migration/dataclasses

# python/migration/importlib-metadata-instead-of-setuptools-at-runtime

# python/ci/use-github-actions

# python/ci/sync-version-matrix-with-requires-python

# python/ci/use-trusted-publishing

Example of something with --yolo


# oops/python/forgot-type-imports

# oops/python/forgot-stdlib-imports

# oops/python/print-stmt-left-in

# oops/python/fmt

Just runs the right version of ruff (or ufmt)?

# oops/python/sort-your-dunder-all

# oops/python/no-more-coding-line

# oops/python/use-generic-shebang

# oops/python/use-version-appropriate-future-imports

Remove ones that are always-on in the min version per `requires_python`

# oops/python/unnecessary-u-prefix

If the formatter doesn't take care of this


# oops/{go,java,js}/fmt

TODO figure out if version needs to be defined in project, and how to fetch
