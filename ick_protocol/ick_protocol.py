"""
The protocol spoken internally by the tool `ick`.

This serves the same purpose as an LSP, but with the ability to encapsulate
multiple linters within one process (for faster startup, and the ability to
only load a file off disk once).



This is basically a simplistic LSP but with the ability to report more information abouty

A typical session goes like:

Ick       Rule
Request ->
      <- HaveLinter
      <- Chunk
      <- Chunk
      <- Finished
...and in case of conflict there will be an additional...
Request (just the conflict DEST filenames) ->
      <- HaveLinter (for good measure)
      <- Chunk
      <- Finished

This is basically a ultra-simplistic LSP, but with the addition that
modifications have dependencies, and multiple linters can run in the same
process (regular LSP just has "format_file").
"""

from __future__ import annotations

from enum import Enum, StrEnum
from typing import Sequence, Union

from msgspec import Struct
from msgspec.structs import replace as replace


class Risk(Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"

    def __lt__(self, other):  # type: ignore[no-untyped-def] # FIX ME
        return self._sort_order_ < other._sort_order_  # type: ignore[attr-defined] # FIX ME


class Urgency(Enum):
    OPTIONAL = "optional"
    LATER = "later"
    SOON = "soon"
    NOW = "now"
    URGENT = "urgent"

    def __lt__(self, other):  # type: ignore[no-untyped-def] # FIX ME
        return self._sort_order_ < other._sort_order_  # type: ignore[attr-defined] # FIX ME


class Scope(Enum):
    REPO = "repo"
    PROJECT = "project"
    FILE = "file"


class Success(Enum):
    """How a rule's success should be determined."""

    EXIT_STATUS = "exit-status"
    NO_OUTPUT = "no-output"


# Basic API Requests


class Setup(Struct, tag_field="t", tag="S"):
    rule_path: str
    timeout_seconds: int
    collection_name: str | None = None
    # either common stuff, or serialized config


class List(Struct, tag_field="t", tag="L"):
    pass


class Run(Struct, tag_field="t", tag="R"):
    rule_name: str
    working_dir: str


# Basic API Responses


class SetupResponse(Struct, tag_field="t", tag="SR"):
    pass


class ListResponse(Struct, tag_field="t", tag="LR"):
    rule_names: Sequence[str]


class Modified(Struct, tag_field="t", tag="M"):
    rule_name: str
    filename: str
    new_bytes: bytes | None
    additional_input_filenames: Sequence[str] = ()
    diffstat: str | None = None
    diff: str | None = None


class RuleStatus(StrEnum):
    """The end-state of a rule."""

    # If the rule does not run to completion, status=ERROR and the error info
    # is in .message (ERROR, in unittest terms).
    ERROR = "error"

    # If the rule runs to completion and the code is already in the ideal
    # state, then status=SUCCESS (PASS, in unittest terms).
    SUCCESS = "success"

    # If the rule runs to completion and the code needs help, then
    # status=NEEDS_WORK (FAIL, in unittest terms, regardless of whether there
    # are suggested modifications).
    NEEDS_WORK = "needs-work"


class Finished(Struct, tag_field="t", tag="F"):
    rule_name: str
    status: RuleStatus
    # The entire rule is only allowed one message; it's used as the commit
    # message or displayed inline.
    message: str


class RunRuleFinished(Struct, tag_field="t", tag="Y"):
    # just for good measure -- I don't think these will cross paths?
    name: str
    msg: str


Msg = Union[Setup, List, Run, SetupResponse, ListResponse, Modified, Finished]
