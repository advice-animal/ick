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


