# Projects

Projects are detected by the presence of well-known "marker" files that identify
the root of the project.

There are some default types, but you can add to it, for example:

```toml
[project_root_markers]

sphinx = ["docs/conf.py"]
```

(or in `pyproject.toml`)

```toml
[tool.ick.project_root_markers]

sphinx = ["docs/conf.py"]
```

These instruct ick to consider the *parent* of where `conf.py` exists to be a
`sphinx` project (likely in addition to a `python` project per default config).

Projects aren't detected within higher-level projects, so if there happens to be
a `pyproject.toml` in the root of your repo, you might want to specify

```toml
skip_project_root_in_repo_root = true
```

and if the autodetection fails for you, set some of

```
explicit_project_dirs = [...]
ignore_project_dirs = [...]
```

Note that explicit dirs still need to contain markers, so their type can be
inferred.
