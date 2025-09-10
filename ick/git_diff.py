import subprocess
from pathlib import Path
from typing import Iterable

from ick_protocol import Finished, Modified, Msg, RuleStatus

from .sh import run_cmd


def get_diff_messages(msg: str, rule_name: str, workdir: Path) -> Iterable[Msg]:
    buf: list[str] = []
    plus_count = None
    minus_count = None
    filename = ""
    status = RuleStatus.SUCCESS  # all's ok

    def get_chunk() -> Msg:
        new_bytes: bytes | None = None

        try:
            new_bytes = Path(workdir, filename).read_bytes()
        except FileNotFoundError:
            pass

        nonlocal status
        status = RuleStatus.NEEDS_WORK

        return Modified(
            rule_name=rule_name,
            filename=filename,
            additional_input_filenames=(),
            diffstat=f"+{plus_count}-{minus_count}",
            diff="".join(buf),
            new_bytes=new_bytes,
        )

    run_cmd(["git", "add", "."], cwd=workdir)

    # N.b. we do not pass --binary here because we don't really care about the
    # binary diff, and will include the full contents in `new_bytes` above.
    with subprocess.Popen(
        ["git", "diff", "--staged", "--no-prefix", "--no-color"],
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        cwd=workdir,
    ) as proc:
        for line in proc.stdout:  # type: ignore[union-attr] # FIX ME
            if line.startswith("diff --git "):
                if buf:
                    yield get_chunk()
                buf = [line]
                plus_count = 0
                minus_count = 0
                # TODO creation/deletion/move/copy handling
                parts = line.split()
                filename = parts[2] if parts[2] != "/dev/null" else parts[3]
            elif line.startswith("---"):
                buf.append(line)
            elif line.startswith("+++"):
                buf.append(line)
            elif line.startswith("@@"):
                buf.append(line)
            elif line.startswith(" "):
                buf.append(line)
            elif line.startswith("+"):
                plus_count += 1  # type: ignore[operator] # FIX ME
                buf.append(line)
            elif line.startswith("-"):
                minus_count += 1  # type: ignore[operator] # FIX ME
                buf.append(line)
            elif line.startswith("Binary files "):
                pass
            else:
                # This needs to stay for at least 'index' and '\no newline at eof'
                buf.append(line)

    if buf:
        yield get_chunk()

    yield Finished(status=status, rule_name=rule_name, message=msg)
