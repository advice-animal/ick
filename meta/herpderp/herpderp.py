import re
from typing import Optional

from ick.api import Color, single_file_operation

PAT = re.compile("herp(?!derp")


@single_file_operation(color=Color.GREEN)
def fix(filename: str, data: str) -> Optional[str]:
    """
    Replaces non-derp herp with herpderp.
    """
    return PAT.sub(lambda m: m.group(0) + "derp", data)
