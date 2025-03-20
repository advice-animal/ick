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

from enum import Enum, StrEnum, auto
from typing import Optional, Sequence, Union

from msgspec import Struct
from msgspec.structs import replace as replace


class Risk(Enum):
    # These are structured for easier translation to a bit field (IntFlags)
    # later, in case it makes sense for collections in particular to be able to
    # return one of several risk values after actually analyzing your code.

    HIGH = auto()
    MED = auto()
    LOW = auto()

    def __lt__(self, other):
        return self._sort_order_ < other._sort_order_


class Urgency(StrEnum):
    MANUAL = auto()
    LATER = auto()
    SOON = auto()
    NOW = auto()
    NOT_SUPPORTED = auto()

    def __lt__(self, other):
        return self._sort_order_ < other._sort_order_


class Scope(Enum):
    REPO = "repo"
    PROJECT = "project"
    SINGLE_FILE = "single-file"


class Success(Enum):
    EXIT_STATUS = "exit-status"
    NO_OUTPUT = "no-output"


# Basic API Requests


class Setup(Struct, tag_field="t", tag="S"):
    rule_path: str
    timeout_seconds: int
    collection_name: Optional[str] = None
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
    new_bytes: bytes
    additional_input_filenames: Sequence[str] = ()
    diffstat: Optional[str] = None
    diff: Optional[str] = None


class Finished(Struct, tag_field="t", tag="F"):
    rule_name: str
    error: bool
    # the entire rule is only allowed one message; it's used as the commit
    # message or displayed inline.
    message: str


class RunRuleFinished(Struct, tag_field="t", tag="Y"):
    # just for good measure -- I don't think these will cross paths?
    name: str
    msg: str


Msg = Union[Setup, List, Run, SetupResponse, ListResponse, Modified, Finished]
