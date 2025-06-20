# Contributing

(For now, just some notes to ick authors)

## Logging

We use vmodule, which provides extra logging levels.  Use `VLOG_1` to mean "info,
but more" and `VLOG_2` to mean "info, but even more."

DEBUG messages should be only of interest to ick authors, whereas VLOG_1 and
VLOG_2 can be messages understandable to end users about what ick is doing.

For example, if you want to log something including an internal function name,
it should probably be DEBUG, not VLOG_2.

```python
from logging import getLogger
from vmodule import VLOG_1, VLOG_2

LOG = getLogger(__name__)

LOG.info("Reading config now")
LOG.log(VLOG_2, "Looking for a file named blah-blah")
LOG.log(VLOG_1, "Reading file blah-blah")
LOG.debug("Inside read_config_files()")
```
