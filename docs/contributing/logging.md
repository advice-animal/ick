# Logging

We use [vmodule] to provide extra logging levels.  Use `VLOG_1` to mean "info,
but more" and `VLOG_2` to mean "info, but even more."

Debug messages should be only of interest to ick authors, whereas `INFO`,
`VLOG_1`, and `VLOG_2` can be messages understandable to end users about what
ick is doing.

For example, if you want to log something including an internal function name,
it should probably be debug, not `VLOG_2`.

In summary (partially borrowed from the [logging docs][log levels]):

- `CRITICAL`: A serious error, indicating that the program itself may be unable
  to continue running.

- `ERROR`: Due to a serious problem, the software has not been able to perform
  some function.

- `WARNING`: Something unexpected happened, or a problem might occur in the
  near future (for example, "disk space low"). The software is still working as
  expected.

- `INFO`: Information about what ick is doing, in terms the user can
  understand.  This level and below are normally not displayed.

- `VLOG_1`: Like `INFO`, but more detailed.

- `VLOG_2`: Even more detailed!

- `DEBUG`: Internal details only of use to ick developers.

The usual log levels (critical, error, warning, info, and debug) are available
as methods on the logger object.  `VLOG_1` and `VLOG_2` have to be provided as
arguments to logger.log:

```python
from logging import getLogger
from vmodule import VLOG_1, VLOG_2

LOG = getLogger(__name__)

LOG.info("Reading config now")
LOG.log(VLOG_2, "Looking for a file named blah-blah")
LOG.log(VLOG_1, "Reading file blah-blah")
LOG.debug("Inside read_config_files()")
```


[vmodule]: https://pypi.org/project/vmodule/
[log levels]: https://docs.python.org/3/library/logging.html#logging-levels
