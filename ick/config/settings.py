"""
Runtime settings, either from env or flags
"""

from msgspec import Struct

from ick_protocol import Risk, Urgency


class Settings(Struct):
    """
    skip_update: When loading rules from a repo, don't pull if some version already exists locally
    """

    #: Intended to be explicitly set based on flags
    dry_run: bool = True
    #: Intended to be explicitly set based on flags
    apply: bool = False
    #: Intended to be explicitly set based on flags
    isolated_repo: bool = False
    #: Intended to be explicitly set based on flags
    skip_update: bool = False


class FilterConfig(Struct):
    """
    Settings that control what gets run.
    """

    #: Default means "don't filter any names"
    name_filter_re: str = ".*"
    #: Default means "don't filter any production urgencies"
    min_urgency: Urgency = Urgency.LATER
    min_risk: Risk = Risk.HIGH
