from typing import (Set, List, Dict, Tuple, Callable, Optional)
from dataclasses import dataclass
from enum import Enum

FileName=str

@dataclass(frozen=True)
class RunResult:
  """ Result of launchng the readout job """
  fname:FileName     # File where the output data is piped into
  pattern:str        # Termination patter to search for in the output stream.

@dataclass
class ReadResult:
  """ Result of reading from the readout job """
  text:str           # Current contents of the readout file.
  timeout:bool       # Did the current read attmept timeout? If so, Litrepl
                     # would return control to the user with a
                     # continuation-looking result..

NSec=int
CursorPos=Tuple[int,int]

@dataclass
class PrepInfo:
  """ Results of the document preprocessing """
  nsec:NSec                         # Number of code sections
  cursors:Dict[CursorPos,NSec] # Resolved cursor locations
  pending:Dict[NSec,RunResult]      # Async job markers


@dataclass
class SecRec:
  """ Request for section evaluation """
  nsecs:Set[NSec]                   # Sections to evaluate
  pending:Dict[NSec,RunResult]      # Contexts of already running sections

@dataclass
class FileNames:
  """ Interpreter state """
  wd:str                   # Working directory
  inp:str                  # Input pipe
  outp:str                 # Output pipe
  pidf:str                 # File containing PID
  ecodef:str               # File containing exit code


class IType(Enum):
  Python = 0,
  IPython = 1

@dataclass
class Settings:
  """ Interpreter settings to share among the runners """
  itype:IType

