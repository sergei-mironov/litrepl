import re
import os
import sys
import fcntl

from fcntl import LOCK_NB,LOCK_UN,LOCK_EX
from copy import deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable
from re import search, match as re_match, compile as re_compile
from select import select
from os import environ, system, getpid, unlink
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter
from os.path import isfile, join
from signal import signal, SIGINT, SIGALRM, setitimer, ITIMER_REAL
from time import sleep, time
from dataclasses import dataclass, astuple
from functools import partial
from argparse import ArgumentParser
from contextlib import contextmanager
from errno import ESRCH
from signal import (pthread_sigmask, valid_signals, SIG_BLOCK, SIG_UNBLOCK,
                    SIG_SETMASK)

from .types import (LitreplArgs, RunResult, ReadResult, FileNames, EvalState,
                    ECode, ECODE_OK, ECODE_RUNNING, ECODE_UNDEFINED)
from .utils import remove_silent, wraplong, hashdigest, assert_

def pstderr(*args,**kwargs):
  print(*args, file=sys.stderr, **kwargs, flush=True)

DEBUG:bool=False

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f},{getpid()}]", *args, file=sys.stderr, **kwargs, flush=True)

def pusererror(fname,err)->None:
  with open(fname,"w") as f:
    f.write(err)

SIGMASK_NESTED=False

@contextmanager
def with_parent_finally(_handler):
  """ `fork`-safe try-finally context-manager. Executes the `_handler` function
  in a `finally` block, making sure is it executed exactly once, in the process
  that calls the function."""
  pid:int=getpid()
  try:
    yield # Might trigger for a child process
  finally:
    if pid==getpid():
      _handler()

@contextmanager
def with_sigmask(signals=None):
  """ Runs a context code with Posix SIGMASK enabled, preventing `signals` to
  happen. By default disables all valid signals. """
  global SIGMASK_NESTED
  assert_(not SIGMASK_NESTED)
  signals=valid_signals() if signals is None else signals
  old=None
  try:
    old=pthread_sigmask(SIG_SETMASK,signals)
    SIGMASK_NESTED=True
    yield
  finally:
    SIGMASK_NESTED=False
    if old is not None:
      pthread_sigmask(SIG_SETMASK,old)

def readipid(fns:FileNames)->Optional[int]:
  """ Reads a PID of the background interpeter session process from the
  auxiliary directory. """
  try:
    return int(open(fns.pidf).read())
  except (ValueError,FileNotFoundError):
    return None

@contextmanager
def with_sigint(propagate_sigint:bool, fns:FileNames):
  """ Runs a context code with a SIGINT handler which kills the background
  interpreter rahter than the LitRepl itself. """
  ipid=readipid(fns)
  def _handler(signum,frame):
    pdebug(f"Sending SIGINT to {ipid}")
    os.kill(ipid,SIGINT)
  prev=None
  def _finally():
    with with_sigmask():
      if prev is not None:
        signal(SIGINT,prev)
  with with_parent_finally(_finally):
    with with_sigmask():
      if ipid is not None:
        if propagate_sigint:
          prev=signal(SIGINT,_handler)
      else:
        pdebug(f"Failed to read pid: not installing SIGINT handler")
    yield

@contextmanager
def with_alarm(timeout_sec:float):
  """ Set the alarm if the timeout is known. Zero or infinite timeout means no
  timeout is set. """
  def _handler(signum,frame):
    pdebug(f"SIGALARM received")
    raise TimeoutError()

  prev=None
  def _finally():
    if timeout_sec>0 and timeout_sec<float('inf'):
      # pdebug(f"Alarm {timeout_sec} cleaning")
      with with_sigmask():
        if prev is not None:
          setitimer(ITIMER_REAL,0)
          signal(SIGALRM,prev)

  with with_parent_finally(_finally):
    if timeout_sec>0 and timeout_sec<float('inf'):
      with with_sigmask():
        prev=signal(SIGALRM,_handler)
        setitimer(ITIMER_REAL,timeout_sec)
      # pdebug(f"Alarm {timeout_sec} set")
    yield


def merge_basic2(acc,r,x)->Tuple[bytes,int]:
  """ Merges a buffer and a new text without any post-processing. """
  return (acc+r,x)

def merge_rn2(buf_,r,i_n=-1)->Tuple[bytes,int]:
  """ Merges a buffer `buf_` and a newly-arrived text `r`, taking into account
  terminal line-wrapping codes `\\r\\n`. Return a new buffer and
  the position of the last `\\n` in it."""
  buf=deepcopy(buf_)
  sz=len(buf)
  i_n=-(sz-i_n)
  start=0
  for i in range(len(r)):
    if r[i]==10:
      i_n=i
      buf+=r[start:i+1]
      start=i+1
    elif r[i]==13:
      if i_n<0:
        buf=buf[:sz+i_n+1]
        sz=len(buf)
        i_n=-1
      start=i+1
  buf+=r[start:]
  if i_n>=0:
    i_n-=start
  assert_(b'\r' not in buf)
  if i_n>=0:
    assert_(i_n<len(buf), f"{len(buf)}, {i_n}")
    assert_(buf[i_n]==(b'\n'[0]), f"{buf}, {i_n}, {buf[i_n]}")
  return buf,sz+i_n if i_n<0 else sz+i_n


def readout(fdr,
            prompt,
            merge)->str:
  """ Read the `fdr` until the prompt regexp is found. The prompt must define
  exactly one group to query after the match is detected. See `mkre`.
  """
  # [1] - Here we query the single matched group, see `mkre`
  acc:bytes=b''
  i_n=-1
  while select([fdr],[],[],None)[0] != []:
    r=os.read(fdr, 1024)
    if r!=b'':
      acc,i_n=merge(acc,r,i_n)
    m=re_match(prompt,acc)
    if m:
      acc=m.group(1) # [1]
      r=b''
    if r==b'':
      try:
        return acc.decode('utf-8')
      except UnicodeDecodeError:
        return "<LitREPL: Non-unicode output>"
  return "<LitREPL: timeout waiting the interpreter response>"

def readout_asis(fdr:int, fdw:int, fo:int, pattern:str, prompt,
                 timeout:Optional[int]=None)->None:
  """ Read everything from FD `fdr` and send to `fo` until `prompt` is found. If
  the `propmt` is not found within the `timeout` seconds, re-send the `pattern`
  and continue the interaction. This function is intended to be run from a
  separate process, governing the interaction with intepreters.
  """
  acc:bytes=b''
  os.write(fdw,pattern.encode())
  while True:
    rlist = select([fdr],[],[],timeout)[0]
    if rlist == []:
      # pdebug(f"readout_asis timeout, repeating the prompt pattern")
      os.write(fdw,pattern.encode())
    else:
      pdebug(f"readout_asis ready to read")
      r=os.read(fdr, 1024)
      pdebug(f"readout_asis read {len(r)} bytes")
      if r==b'':
        return
      w=os.write(fo,r)
      if w!=len(r):
        os.write(fo,"<LitREPL failed to copy input stream>\n".encode())
        # assert True
      acc+=r # TODO: don't store everything
      m=re_match(prompt,acc)
      if m:
        return

TIMEOUT_SEC=3

def mkre(prompt:str):
  """ Matches the shortest string followed by a sequence of prompts """
  return re_compile(f"((.(?!{prompt}))*(.(?={prompt}))?)({prompt})+".encode('utf-8'),
                    re.MULTILINE|re.DOTALL)


def interact(fdr, fdw, text:str, fo:int, ss:Interpreter)->None:
  """ Interpreter interaction procedure, running in a forked process. Its goal
  is to sent the code to the interpreter, to read the response and, most
  importantly, to detect when to stop reading.

  Args:
    fdr (int): Interpreter's stdout pipe, available for reading
    fdw (int): Interpreter's stdin pipe, available for writing
    text (str): Text to send to the interpreter
    fo (int): Output desctiptor, available for writing
    ss (Interpreter): Interpreter abstraction object
  """
  p1,p2=ss.patterns()
  os.write(fdw,p1[0].encode())
  x=readout(fdr,prompt=mkre(p1[1]),merge=merge_rn2)
  pdebug(f"interact readout returned '{x}'")
  os.write(fdw,text.encode())
  os.write(fdw,'\n'.encode())
  pdebug(f"interact main text ({len(text)} chars) sent")
  readout_asis(fdr,fdw,fo,p2[0],prompt=mkre(p2[1]),timeout=TIMEOUT_SEC)

def process(a:LitreplArgs,fns:FileNames, ss:Interpreter, lines:str)->Tuple[str,RunResult]:
  """ Evaluate `lines` synchronously. """
  pdebug("process started")
  p1,p2=ss.patterns()
  runr=processAsync(fns,ss,lines)
  res=''
  with with_sigint(a.propagate_sigint,fns):
    with with_locked_fd(runr.fname,OPEN_RDONLY,LOCK_EX) as fdr:
      assert_(fdr is not None)
      pdebug("process readout")
      res=readout(fdr,prompt=mkre(p2[1]),merge=merge_rn2)
      remove_silent(runr.fname)
      pdebug("process readout complete")
  return res,runr

def interpIsRunning(fns:FileNames)->bool:
  """ Is the background interpreter session running?"""
  try:
    ipid=readipid(fns)
    if ipid is None:
      return False
    os.kill(ipid, 0)
  except OSError as err:
    if err.errno == ESRCH:
      return False
  return True

def interpExitCode(fns:FileNames,
                   poll_sec=0.5,
                   poll_attempts=4,
                   undefined=ECODE_UNDEFINED)->ECode:
  """ Determines retcode of the interpreter. Polls it a little if it looks
  crashed."""
  ecode:int|None=None
  while ecode is None:
    if interpIsRunning(fns):
      return ECODE_RUNNING
    else:
      try:
        return int(open(fns.ecodef).read())
      except (ValueError,FileNotFoundError):
        pass
    poll_attempts-=1
    if poll_attempts<=0:
      break
    sleep(poll_sec)
  return undefined

@contextmanager
def with_fd(name:str, flags:int, open_timeout_sec=float('inf')):
  fd=None
  def _finally():
    pdebug(f"Closing {name}")
    with with_sigmask():
      if fd is not None:
        os.close(fd)
  with with_parent_finally(_finally):
    try:
      with with_alarm(open_timeout_sec):
        with with_sigmask(valid_signals()-{SIGALRM}):
          fd=os.open(name,flags)
      pdebug(f"Opened {name}")
      assert_(fd>0, f"Failed to open file '{name}', retcode: {fd}")
      yield fd
    except TimeoutError:
      pdebug(f"Unable to open {name}")
      yield None

@contextmanager
def with_locked_fd(name:str, flags:int, lock_flags:int,
                   open_timeout_sec=float('inf'), lock_timeout_sec=float('inf')):
  with with_fd(name,flags,open_timeout_sec) as fd:
    if fd:
      try:
        with with_alarm(lock_timeout_sec):
          fcntl.flock(fd,lock_flags)
        yield fd
      except TimeoutError:
        pdebug(f"Alarm while locking {name}")
        yield None
      except BlockingIOError as err:
        pdebug(f"Unable to lock {name}", err)
        yield None
    else:
      yield None

def read_nonblock(file:str, size=1024)->str:
  # FIXME: move to utils.py
  try:
    with with_fd(file,os.O_RDONLY|os.O_NONBLOCK) as fd:
      if fd is not None:
        return os.read(fd,size).decode('utf-8')
      else:
        return "<Failed to open last error messages>"
  except Exception as e:
    return f"<Failed to read last error message: {str(e)}>"

CREATE_WRONLY_EMPTY=os.O_WRONLY|os.O_SYNC|os.O_TRUNC|os.O_CREAT
OPEN_RDONLY=os.O_RDONLY|os.O_SYNC
LOCK_NONBLOCKING=LOCK_EX|LOCK_NB
LOCK_BLOCKING=LOCK_EX

def processAsync(fns:FileNames, ss:Interpreter, code:str)->RunResult:
  """ Send `code` to the interpreter and fork the response reader. The output
  file is locked and its name is saved into the resulting `RunResult` object.
  """
  wd,inp,outp,_,_,_=astuple(fns)
  codehash=hashdigest(code)
  fname=join(wd,f"partial_{codehash}.txt")
  pdebug(f"processAsync starting via {fname}")
  with with_locked_fd(fname,CREATE_WRONLY_EMPTY,LOCK_NONBLOCKING) as fo:
    if fo is not None:
      sys.stdout.flush(); sys.stderr.flush() # FIXME: crude
      pid=os.fork()
      if pid==0:
        # Child
        sys.stdout.close(); sys.stdin.close()
        def _handler(signum,frame):
          pass
        signal(SIGINT,_handler)
        pdebug(f"processAsync reader opening pipes")
        with with_locked_fd(inp, os.O_WRONLY|os.O_SYNC,
                            fcntl.LOCK_EX|fcntl.LOCK_NB,open_timeout_sec=0.5) as fdw:
          with with_locked_fd(outp, os.O_RDONLY|os.O_SYNC,
                              fcntl.LOCK_EX|fcntl.LOCK_NB,open_timeout_sec=0.5) as fdr:
            if fdw and fdr:
              pdebug("processAsync reader interact start")
              try:
                interact(fdr,fdw,code,fo,ss)
                pdebug("processAsync reader interact finish")
              except BrokenPipeError:
                pdebug("processAsync catches Broken Pipe error")
                os.write(fo,"<BrokenPipe>\n".encode())
                raise
            else:
              # FIXME: We must transfer error back to the reader to be able to
              # exit with an errorcode.
              os.write(fo,"<Unable to access the interpreter>\n".encode())
        pdebug("Exiting!")
        exit(0)
      else:
        # Parent
        pdebug(f"processAsync parent forked {pid}")
        return RunResult(fname)
    else:
      # The reader is already running, try to own it.
      pdebug(f"processAsync re-uses already existing reader")
      return RunResult(fname)

def processCont(fns:FileNames,
                ss:Interpreter,
                runr:RunResult,
                timeout:float,
                propagate_sigint:bool)->ReadResult:
  """ Read from the running readout process. """
  rr:Optional[ReadResult]=None
  p1,p2=ss.patterns()
  with with_sigint(propagate_sigint,fns):
    pdebug(f"processCont starting via {runr.fname}")
    with with_locked_fd(runr.fname,
                        os.O_RDONLY|os.O_SYNC,
                        LOCK_BLOCKING if timeout>0 else LOCK_NONBLOCKING,
                        lock_timeout_sec=timeout) as fdr:

      if fdr:
        pdebug(f"processCont final readout start")
        res=readout(fdr,prompt=mkre(p2[1]),merge=merge_rn2)
        pdebug(f"processCont final readout finish")
        rr=ReadResult(res,False) # Return final result
        remove_silent(runr.fname)
        pdebug(f"processCont unlinked {runr.fname}")
      else:
        with with_fd(runr.fname,os.O_RDONLY|os.O_SYNC) as fdr:
          assert_(fdr is not None)
          pdebug("processCont readout(nonblocking) start")
          res=readout(fdr,prompt=mkre(p2[1]),merge=merge_rn2)
          pdebug(f"processCont readout(nonblocking) finish")
          rr=ReadResult(res,True) # Timeout ==> Return continuation
  assert_(rr is not None)
  return rr

def processAdapt(fns:FileNames,
                 ss:Interpreter,
                 code:str,
                 timeout:float=1.0,
                 propagate_sigint:bool=True)->Tuple[ReadResult,RunResult]:
  """ Push `code` to the interpreter and wait for `timeout` seconds for
  the immediate answer. In case of delay, return intermediate answer and
  the continuation context."""
  # if timeout == float('inf'):
  #   lines2,runr=process(fns,ss,code)
  #   return ReadResult(lines2,False),runr
  # else:
  runr=processAsync(fns,ss,code)
  rr=processCont(fns,ss,runr,timeout=timeout,propagate_sigint=propagate_sigint)
  return rr,runr

# LitRepl pending evaluation tag regexp
PRESULT_RE=re_compile(r"(.*)\[LR:([a-zA-Z0-9_\/\.-]+)\]\s*$",
                      re.A|re.DOTALL)

def rresultLoad(text:str)->Tuple[str,Optional[RunResult]]:
  """ Loads the contents of a result section from the input document. Parse
  LitrRepl tags, if any. Return the result text along with the RunResult."""
  m=re_match(PRESULT_RE,text)
  if m:
    return (m[1],RunResult(m[2]))
  else:
    return text,None

def rresultSave(text:str, presult:RunResult)->str:
  """ Saves uncompleted RunRestult into the response text in order to load and
  check it later. """
  sep='\n' if text and text[-1]!='\n' else ''
  return (text+f"{sep}[LR:{presult.fname}]\n")

def interp_code_preprocess(a:LitreplArgs, ss:Interpreter, es:EvalState, code:str) -> str:
  return ss.code_preprocess(a,es,code)

def interp_result_postprocess(a:LitreplArgs, ss:Interpreter, text:str) -> str:
  s=ss.result_postprocess(a,text)
  return wraplong(s,a.result_textwidth) if a.result_textwidth else s

def eval_code(*args, **kwargs) -> str:
  """ Start or complete the code section evaluation, return a response to be
  printed to the output document. See `eval_code_` for details. """
  res,_=eval_code_(*args, **kwargs)
  return res

def eval_code_(a:LitreplArgs,
               fns:FileNames,
               ss:Interpreter,
               es:EvalState,
               code:str,
               runr:Optional[RunResult]=None) -> Tuple[str,ReadResult]:
  """ Start or complete the code section evaluation. `runr`
  contains the already existing runner's context, if any.

  The function returns either the evaluation result or the running context
  encoded in the result for later reference.
  """
  rr:ReadResult
  rr,runr=eval_code_raw(ss,interp_code_preprocess(a,ss,es,code),
                        a.timeout_initial,a.timeout_continue,a.propagate_sigint,runr)
  pptext=interp_result_postprocess(a,ss,rr.text)
  res=rresultSave(pptext,runr) if rr.timeout else pptext
  return res,rr

def eval_code_raw(ss:Interpreter,
                  code:str,
                  timeout_initial,
                  timeout_continue,
                  propagate_sigint,
                  runr:Optional[RunResult]=None) -> Tuple[ReadResult,RunResult]:
  """ Start or complete the code section evaluation without pre- and
  post-processing. See also `eval_code_`. """
  fns=ss.fns
  if runr is None:
    rr,runr=processAdapt(fns,ss,code,timeout_initial,propagate_sigint)
  else:
    rr=processCont(fns,ss,runr,timeout_continue,propagate_sigint)
  return rr,runr

