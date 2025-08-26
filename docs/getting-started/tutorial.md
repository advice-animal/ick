<!--
    This file has embedded Python code that must be run to keep it up-to-date.
    Use `make prepdocs` to run it.

    [[[cog
        import os
        from cog_helpers import *
        set_source_root("docs/data/tutorial")
        cd_temp(pretend="/tmp/tut")
        os.environ["ICK_ISOLATED_REPO"] = "1"
    ]]]
    [[[end]]] (sum: 1B2M2Y8Asg)
-->

# Tutorial

Ick coordinates the running of automated rules on your code and other files.
Rules can check for conformance, or can transform your files to apply needed
modifications.

Rules can be sourced from many places: your code's repo, a rules repo of your
own, a rules repo provided by someone else, or even a local directory.  Ick lets
you use rules from a number of sources at once.

For this tutorial, we'll be using two repos.  The first will stand in for your
code: the code you want to analyze or modify with ick.  To start, clone this
dead-simple repo:

<!-- [[[cog
        show_cmd(
            "git clone https://github.com/advice-animal/ick-tutorial-sample-1",
            "cd ick-tutorial-sample-1",
        )
    ]]] -->
```console
$ git clone https://github.com/advice-animal/ick-tutorial-sample-1
Cloning into 'ick-tutorial-sample-1'...
$ cd ick-tutorial-sample-1
```
<!-- [[[end]]] (sum: RimKp2Mp9W) -->

This repo only has a few files:

<!-- [[[cog show_tree(".") ]]]-->
```console
├── README.md
├── isort.cfg
└── pyproject.toml
```
<!-- [[[end]]] (sum: Hby/Xig7nS) -->

The simple rule we'll demonstrate moves isort settings from the isort.cfg file
into the pyproject.toml file.  That rule is in our [second repo][tutrules], but
you don't need to clone it.  We'll refer to it with the `--rule-repo` option for
ick.

[tutrules]: https://github.com/advice-animal/ick-tutorial-rules-1

Ick can show us the rules available:

<!-- [[[cog show_cmd("ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 list-rules") ]]] -->
```console
$ ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 list-rules
LATER
=====
* ick-tutorial-rules-1/move_isort_cfg
```
<!-- [[[end]]] (sum: dE4lCr/W8Q) -->

If we run the rules, ick is cautious and shows diff stats of what would change,
but no files are changed:

<!-- [[[cog show_cmd("ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 run") ]]] -->
```console
$ ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 run
-> ick-tutorial-rules-1/move_isort_cfg: NEEDS_WORK
     isort.cfg -3
     pyproject.toml +4
```
<!-- [[[end]]] (sum: fVKYlqzvgM) -->

This shows that isort.cfg would have three lines deleted, and pyproject.toml
would have four lines added.

To see the full diff, use the `--patch` option:

<!-- [[[cog show_cmd("ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 run --patch") ]]] -->
```console
$ ick --rules-repo=https://github.com/advice-animal/ick-tutorial-rules-1 run --patch
-> ick-tutorial-rules-1/move_isort_cfg: NEEDS_WORK
--- a/isort.cfg
+++ b/isort.cfg
@@ -1,3 +0,0 @@
-[settings]
-line_length = 88
-multi_line_output = 3
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,3 +1,7 @@
 [project]
 name = "tutorial-sample"
 description = "A simple bare-bones repo for a tutorial"
+
+[tool.isort]
+line_length = "88"
+multi_line_output = "3"
```
<!-- [[[end]]] (sum: wdAW9vS7jk) -->

[WHAT ELSE SHOULD GO HERE?]


## Writing rules

Next up if you interested: how to write rules, demonstrated in the [Writing
rules Tutorial](writing-tutorial.html).

<!-- splitme1 -->
