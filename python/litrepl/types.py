import re
from typing import (Any, Set, List, Dict, Tuple, Callable, Optional)
from re import compile as re_compile
from dataclasses import dataclass
from enum import Enum

FileName=str
LitreplArgs=Any

# Process exit code or None (running)
ECode=Optional[int]
ECODE_RUNNING=None
ECODE_OK=0
ECODE_UNDEFINED=255

class SType(Enum):
  """ Code section types """
  SPython = 0
  SAI = 1

class IType(Enum):
  """ Interpreter types """
  # FIXME: use `Interpreter` classes insted
  Python = 0,
  IPython = 1
  GPT4AllCli = 2

@dataclass(frozen=True)
class RunResult:
  """ Result of launchng the readout job """
  fname:FileName     # File where the output data is piped into

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
  nsec:NSec                         # Total number of code sections
  cursors:Dict[CursorPos,NSec]      # Sections, resolved from cursor positions
  pending:Dict[NSec,RunResult]      # Async job markers
  results:Dict[NSec,str]            # Results

  @staticmethod
  def empty():
    return PrepInfo(0,{},{},{})

@dataclass
class SecRec:
  """ Request for section evaluation """
  nsecs:Set[NSec]                   # Sections to evaluate
  preproc:PrepInfo                  # Results of preprocessing

  @staticmethod
  def empty():
    return SecRec(set(),PrepInfo.empty())

@dataclass
class FileNames:
  """ Interpreter state """
  wd:str                            # Working directory
  inp:str                           # Input pipe
  outp:str                          # Output pipe
  pidf:str                          # File containing PID
  ecodef:str                        # File containing exit code


@dataclass
class Settings:
  """ Interpreter settings to share among the runners """
  itype:IType
  pattern1:Tuple[str,str]           # Request-response pair 1
  pattern2:Tuple[str,str]           # Request-response pair 2

SECVAR_RE = re_compile("(\^+ *R[0-9]+ *\^+)|(v+ *R[0-9]+ *v+)|(\>+ *R[0-9]+ *\<+)",
                       flags=re.MULTILINE|re.A)


@dataclass
class EvalState:
  """ Interpreter state, tracking evaluation of document sections """
  sr:SecRec                         # The original request
  sres:Dict[int,str]                # Section results: sec.num -> result
  ledder:Dict[int,int]              # Facility to restore the cursor: line -> offset
  ecodes:Dict[int,ECode]            # Exit codes: sec.num -> exitcode
  stypes:Set[SType]                 # Section types we have already run
  nsec:int                          # Current section

  def __init__(self,sr:SecRec):
    self.sr,self.sres,self.ledder,self.ecodes,self.stypes,self.nsec=sr,{},{},{},set(),-1



