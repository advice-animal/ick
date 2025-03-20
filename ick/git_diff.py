import subprocess
from pathlib import Path
from typing import Optional

from ick_protocol import Finished, Modified


def get_diff_messages(msg, rule_name: str, workdir: Path):
    buf = []
    plus_count = None
    minus_count = None
    filename = None

    def get_chunk():
        new_bytes: Optional[bytes] = None

        try:
            new_bytes = Path(workdir, filename).read_bytes()
        except FileNotFoundError:
            pass

        return Modified(
            rule_name=rule_name,
            filename=filename,
            additional_input_filenames=(),
            diffstat=f"+{plus_count}-{minus_count}",
            diff="".join(buf),
            new_bytes=new_bytes,
        )

    # N.b. we do not pass --binary here because we don't really care about the
    # binary diff, and will include the full contents in `new_bytes` above.
    with subprocess.Popen(
        ["git", "diff", "--no-prefix", "--no-color"],
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        cwd=workdir,
    ) as proc:
        for line in proc.stdout:
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
                plus_count += 1
                buf.append(line)
            elif line.startswith("-"):
                minus_count += 1
                buf.append(line)
            elif line.startswith("Binary files "):
                pass
            else:
                # This needs to stay for at least 'index' and '\no newline at eof'
                buf.append(line)

    if buf:
        yield get_chunk()

    yield Finished(error=False, rule_name=rule_name, message=msg)
