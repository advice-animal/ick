# Overview

Ick coordinates the execution of rules that check and/or modify code.  Rules can
be written in any language, using any tooling they need.  Ick's philosophy is to
meet you where you are: if you have code analysis and modification tools at
hand, you can use them to write a rule for use with ick.

A key idea about ick rules is they are not tied to ick: you can write, test, and
run your rule as a standalone program.  Ick offers support for running your
rules in a coordinated and isolated way, and for running tests you can provide,
but the rule can still be easily run on its own.  This gives you more
flexibility in development and keeps ick simpler.

- things to keep in mind when writing rules
- the structure of a rule
