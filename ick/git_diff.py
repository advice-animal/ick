import subprocess
from pathlib import Path
from typing import Optional

from ick_protocol import Finished, Modified

from .sh import run_cmd


def get_diff_messages(msg, rule_name: str, workdir: Path):  # type: ignore[no-untyped-def] # FIX ME
    buf = []  # type: ignore[var-annotated] # FIX ME
    plus_count = None
    minus_count = None
    filename = None

    def get_chunk():  # type: ignore[no-untyped-def] # FIX ME
        new_bytes: Optional[bytes] = None

        try:
            new_bytes = Path(workdir, filename).read_bytes()  # type: ignore[arg-type] # FIX ME
        except FileNotFoundError:
            pass

        return Modified(
            rule_name=rule_name,
            filename=filename,  # type: ignore[arg-type] # FIX ME
            additional_input_filenames=(),
            diffstat=f"+{plus_count}-{minus_count}",
            diff="".join(buf),
            new_bytes=new_bytes,  # type: ignore[arg-type] # FIX ME
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
                    yield get_chunk()  # type: ignore[no-untyped-call] # FIX ME
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
        yield get_chunk()  # type: ignore[no-untyped-call] # FIX ME

    yield Finished(error=False, rule_name=rule_name, message=msg)
