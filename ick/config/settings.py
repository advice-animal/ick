"""
Runtime settings, either from env or flags
"""

from msgspec import Struct

from ick_protocol import Risk, Urgency


class Settings(Struct):
    """
    There are three combinations of this that make sense:

    dry_run=True, yolo=False: Tell me what needs to be changed
    dry_run=False, yolo=False: Make (safe) changes here
    dry_run=False, yolo=True: Make (safe+unsafe) changes here
    """

    #: Intended to be explicitly set based on flags
    dry_run: bool = True
    #: Intended to be explicitly set based on flags
    yolo: bool = False
    #: Intended to be explicitly set based on flags
    isolated_repo: bool = False


class FilterConfig(Struct):
    """
    Settings that control what gets run.
    """

    #: Default means "don't filter any names"
    name_filter_re: str = ".*"
    #: Default means "don't filter any production urgencies"
    min_urgency: Urgency = Urgency.LATER
    min_risk: Risk = Risk.HIGH
