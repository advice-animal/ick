# Manual testing

Codemods such as ick rules are meant to run automatically on many files. Those
files have differences that can affect how well your rule works.  Because of
this, it's important to test your rules on a variety of real-world examples.

Manually testing your rules on sample repositories is a good way to get a feel
for how well your rules work and to find edge cases you might not have
considered.

## Running rules from a rules repo

Ick registers rules through `ick.toml` files that it can find in a number of
places. When you are working on a rule, you probably don't want to run all of
those rules. Ick's `--rules-repo` option specifies a single rule repo to use,
sides-stepping all other rules.

If you are in the working tree of your rule repo, you can run your rules against
some other repo like this:

```bash
ick --rules-repo=. --target=/path/to/sample/repo run
```

Ick will find the rules in any `ick.toml` file in the repo. Rules will be named
based on their directory name and the rule name in the `ick.toml` file. Run this
command to list the rules found and their names:

```bash
ick --rules-repo=. list-rules
```

You can filter which rules to run by providing rule names or prefixes after the
command. For example, to run only `my_rule`:

```bash
ick --rules-repo=. --target=/path/to/sample/repo run my_rule
```

As before, `list-rules` can be used to see what rules would be selected.


## Running rules in a sample repo

You can also run your rules manually in a sample repo. Use the `--rules-repo`
option to point to your rule repo, and run the rules like this:

```bash
ick --rules-repo=/path/to/rule/repo run
```

Now the current directory is implicitly the target repo. The rules are read from
the rules repo and use the repo name as the prefix. Use `list-rules` to see the
rule names.

Running in the sample repo is helpful so that you can see the file changes
directly.  Use `run --apply` to have ick modify the files in place.
