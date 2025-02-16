"""
The protocol spoken internally by the tool `ick`.

This serves the same purpose as an LSP, but with the ability to encapsulate
multiple linters within one process (for faster startup, and the ability to
only load a file off disk once).



This is basically a simplistic LSP but with the ability to report more information abouty

A typical session goes like:

Ick       Hook
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

from enum import IntEnum
from typing import Optional, Sequence, Union

from msgspec import Struct
from msgspec.structs import replace as replace

# Basic linter qualifications (these numbers are fixed in stone!)


class Risk(IntEnum):
    # These are structured for easier translation to a bit field (IntFlags)
    # later, in case it makes sense for collections in particular to be able to
    # return one of several risk values after actually analyzing your code.

    HIGH = 1
    MED = 2
    LOW = 4


class Urgency(IntEnum):
    MANUAL = 0
    LATER = 10
    SOON = 20
    NOW = 30
    NOT_SUPPORTED = 40


class Scope(IntEnum):
    REPO = 1
    PROJECT = 2
    SINGLE_FILE = 3


# Basic API Requests


class Setup(Struct, tag_field="t", tag="S"):
    hook_path: str
    timeout_seconds: int
    collection_name: Optional[str] = None
    # either common stuff, or serialized config


class List(Struct, tag_field="t", tag="L"):
    pass


class Run(Struct, tag_field="t", tag="R"):
    hook_name: str
    working_dir: str


# Basic API Responses


class SetupResponse(Struct, tag_field="t", tag="SR"):
    pass


class ListResponse(Struct, tag_field="t", tag="LR"):
    hook_names: Sequence[str]


class Modified(Struct, tag_field="t", tag="M"):
    hook_name: str
    filename: str
    new_bytes: bytes
    additional_input_filenames: Sequence[str] = ()
    diffstat: Optional[str] = None
    diff: Optional[str] = None


class Finished(Struct, tag_field="t", tag="F"):
    hook_name: str
    error: bool
    # the entire hook is only allowed one message; it's used as the commit
    # message or displayed inline.
    message: str


class RunHookFinished(Struct, tag_field="t", tag="Y"):
    # just for good measure -- I don't think these will cross paths?
    name: str
    msg: str


Msg = Union[Setup, List, Run, SetupResponse, ListResponse, Modified, Finished]
