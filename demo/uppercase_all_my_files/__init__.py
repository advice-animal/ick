"""
# Uppercase all my files

This is an example of a simple hook that operates at the `single-file` (the
default) scope.  It is something that you might use with `xargs`, and is a
close match to how pre-commit uses its hooks.

## How it works

1. The working dir will be that of the project (or worst case, repo root)
2. You will be given relative filenames on argv -- this might be a subset of
   the total files.
3. You're not allowed to *modify* external state unless you specify
   `external_state = true` in the config.    You can read external state all
   you want, but modifying requires more user intent (either specifying the
   name of the hook verbatim, or passing `--yolo` on the command line.
4. All information about the `risk` or `prio` now live in the config.

## Env vars

"""

import sys
from pathlib import Path


def main(filenames):
    for f in filenames:
        p = Path(f)
        # N.b. this will fail if given binary files!
        contents = p.read_text()
        new_contents = contents.upper()
        p.write_text(new_contents)


if __name__ == "__main__":
    main(sys.argv[1])
