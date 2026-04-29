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
    #: Legacy prefix-aware fallback, compared against slash-joined names.
    legacy_name_filter_re: str = ".*"
    #: If true, use the legacy prefix-aware matcher instead of the new one.
    allow_legacy_name_filter: bool = False
    #: Default means "don't filter any production urgencies"
    min_urgency: Urgency = Urgency.LATER
    min_risk: Risk = Risk.HIGH
