from typing import (Set, List, Dict, Tuple, Callable, Optional)
from dataclasses import dataclass

FileName=str

@dataclass(frozen=True)
class RunResult:
  """ Result of launchng the readout job """
  fname:FileName     # File to read the incoming data from.
  pattern:str        # Terminate patter.

@dataclass
class ReadResult:
  """ Result of reading from the readout job """
  text:str           # Current contents of the readout file.
  timeout:bool       # Did the read timeout?

NSec=int

@dataclass
class PrepInfo:
  """ Data extracted while preprocessing the document """
  nsec:NSec                         # Number of code sections
  cursors:Dict[Tuple[int,int],NSec] # Resolved cursor locations
  pending:Dict[NSec,RunResult]      # Async job markers


@dataclass
class SecRec:
  """ Request for section evaluation """
  nsecs:Set[NSec]
  pending:Dict[NSec,RunResult]
