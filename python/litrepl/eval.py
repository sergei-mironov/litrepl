import re
import os
import sys
import fcntl

from fcntl import LOCK_NB,LOCK_UN,LOCK_EX
from copy import deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable
from re import search, match as re_match
from select import select
from os import environ, system
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter
from os.path import isfile, join
from signal import signal, SIGINT, SIGALRM, setitimer, ITIMER_REAL
from time import sleep, time
from dataclasses import dataclass, astuple
from functools import partial
from argparse import ArgumentParser
from contextlib import contextmanager

from .types import RunResult, ReadResult, FileNames

def pstderr(*args,**kwargs):
  print(*args, file=sys.stderr, **kwargs, flush=True)

DEBUG:bool=False

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f}]", *args, file=sys.stderr, **kwargs, flush=True)

def pusererror(fname,err)->None:
  with open(fname,"w") as f:
    f.write(err)

@contextmanager
def with_sigint(fns:FileNames, brk=False,ipid:Optional[int]=None):
  ipid_=int(open(fns.pidf).read()) if ipid is None else ipid
  def _handler(signum,frame):
    pdebug(f"Sending SIGINT to {ipid_}")
    os.kill(ipid_,SIGINT)
  prev=signal(SIGINT,_handler)
  try:
    yield
  finally:
    signal(SIGINT,prev)

@contextmanager
def with_alarm(timeout:float):
  """ Set the alarm if the timeout is known. Zero or infinite timeout means no
  timeout is set. """
  prev=None
  try:
    if timeout>0 and timeout<float('inf'):
      def _handler(signum,frame):
        pdebug(f"SIGALARM received")
        raise TimeoutError()
      prev=signal(SIGALRM,_handler)
      setitimer(ITIMER_REAL,timeout)
    yield
  finally:
    if prev is not None:
      setitimer(ITIMER_REAL,0)
      signal(SIGALRM,prev)


def merge_basic2(acc,r,x)->Tuple[bytes,int]:
  return (acc+r,x)

def merge_rn2(buf_,r,i_n=-1)->Tuple[bytes,int]:
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
  assert b'\r' not in buf
  if i_n>=0:
    assert i_n<len(buf), f"{len(buf)}, {i_n}"
    assert buf[i_n]==(b'\n'[0]), f"{buf}, {i_n}, {buf[i_n]}"
  return buf,sz+i_n if i_n<0 else sz+i_n

def mkre(prompt:str):
  """ Create the regexp that matches everything ending with a `prompt` """
  return re.compile(f"(.*)(?={prompt})|{prompt}".encode('utf-8'),
                    re.A|re.MULTILINE|re.DOTALL)


def readout(fdr,
            prompt=mkre('>>>'),
            merge=merge_basic2)->str:
  acc:bytes=b''
  i_n=-1
  while select([fdr],[],[],None)[0] != []:
    r=os.read(fdr, 1024)
    if r!=b'':
      acc,i_n=merge(acc,r,i_n)
    m=re_match(prompt,acc)
    if m:
      acc=m.group(1)
      r=b''
    if r==b'':
      try:
        return acc.decode('utf-8')
      except UnicodeDecodeError:
        return "<LitREPL: Non-unicode output>"
  return "<LitREPL: timeout waiting the interpreter response>"

def readout_asis(fdr:int, fdw:int, fo:int, pattern, prompt,
                 timeout:Optional[int]=None)->None:
  """ Read everything from FD `fdr` and send to `fo` until `prompt` is found. If
  the `propmt` is not found within the `timeout` seconds, re-send the `pattern`
  and continue working the interaction. This function is intended to be run from
  a separate process, governing the process of interaction with an intepreter.
  """
  acc:bytes=b''
  os.write(fdw,pattern.encode())
  while True:
    rlist = select([fdr],[],[],timeout)[0]
    if rlist == []:
      pdebug(f"readout_asis timeout, repeating the query")
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

PATTERN1='325674801010\n'
PATTERN='3256748426384\n'
TIMEOUT_SEC=3

def interact(fdr, fdw, text:str, fo:int, pattern)->None:
  os.write(fdw,PATTERN1.encode())
  x=readout(fdr,prompt=mkre(PATTERN1),merge=merge_rn2)
  pdebug(f"interact readout returned '{x}'")
  os.write(fdw,text.encode())
  os.write(fdw,'\n'.encode())
  pdebug(f"interact main text ({len(text)} chars) sent")
  readout_asis(fdr,fdw,fo,pattern,prompt=mkre(pattern),timeout=TIMEOUT_SEC)

def process(fns:FileNames, lines:str)->str:
  """ Evaluate `lines` synchronously. """
  pdebug("process started")
  r=processAsync(fns, lines)
  fdr=0
  try:
    with with_sigint(fns):
      fdr=os.open(r.fname,os.O_RDONLY|os.O_SYNC)
      assert fdr>0
      fcntl.flock(fdr,LOCK_EX)
      pdebug("process readout")
      res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
      pdebug("process readout complete")
      return res
  finally:
    if fdr!=0:
      os.close(fdr)

def processAsync(fns:FileNames, code:str)->RunResult:
  """ Send `code` to the interpreter and fork the response reader. The output
  file is locked and its name is saved into the resulting `RunResult` object.
  """
  wd,inp,outp,pidf=astuple(fns)
  codehash=abs(hash(code))
  fname=join(wd,f"litrepl_eval_{codehash}.txt")
  pdebug(f"processAsync starting via {fname}")
  pattern=PATTERN
  fo=os.open(fname,os.O_WRONLY|os.O_SYNC|os.O_TRUNC|os.O_CREAT)
  assert fo>0
  fcntl.flock(fo,fcntl.LOCK_EX|fcntl.LOCK_NB)
  # pstderr('Got a write lock')
  sys.stdout.flush(); sys.stderr.flush() # FIXME: crude
  pid=os.fork()
  if pid==0:
    # Child
    fdr=0; fdw=0
    try:
      pdebug(f"processAsync opening pipes")
      fdw=os.open(inp, os.O_WRONLY|os.O_SYNC)
      fdr=os.open(outp, os.O_RDONLY|os.O_SYNC)
      if fdw<0 or fdr<0:
        pusererror(fname,f"ERROR: litrepl.py couldn't open session pipes\n")
      fcntl.flock(fdw,fcntl.LOCK_EX|fcntl.LOCK_NB)
      fcntl.flock(fdr,fcntl.LOCK_EX|fcntl.LOCK_NB)
      def _handler(signum,frame):
        pass
      signal(SIGINT,_handler)
      pdebug("processAsync interact start")
      interact(fdr,fdw,code,fo,pattern)
      pdebug("processAsync interact finish")
    except BlockingIOError:
      pusererror(fname,"ERROR: litrepl.py couldn't lock the sessions pipes\n")
    finally:
      if fo!=0:
        fcntl.fcntl(fo,fcntl.LOCK_UN)
        os.close(fo)
      if fdr!=0:
        os.close(fdr)
      if fdw!=0:
        os.close(fdw)
    exit(0)
  else:
    # Parent
    pdebug(f"processAsync forked reader {pid}")
    fcntl.fcntl(fo,fcntl.LOCK_UN)
    os.close(fo)
    return RunResult(fname,pattern)

def processCont(fns:FileNames, r:RunResult, timeout:float=1.0)->ReadResult:
  """ Read from the running readout process. """
  fdr=0
  rr:ReadResult
  try:
    with with_sigint(fns):
      pdebug(f"processCont started via {r.fname}")
      fdr=os.open(r.fname,os.O_RDONLY|os.O_SYNC)
      assert fdr>0
      try:
        with with_alarm(timeout):
          # Raises exception immediately if used with zero timeout. Waits for
          # the lock with non-zero or infinite timeout.
          fcntl.flock(fdr,LOCK_EX|(0 if timeout>0 else LOCK_NB))
        pdebug(f"processCont final readout start")
        res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
        pdebug(f"processCont final readout finish")
        rr=ReadResult(res,False)
        os.unlink(r.fname)
        pdebug(f"processCont unlinked {r.fname}")
      except (BlockingIOError,TimeoutError):
        pdebug("processCont readout(nonblocking) start")
        res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
        pdebug(f"processCont readout(nonblocking) finish")
        rr=ReadResult(res,True)
      return rr
  finally:
    if fdr!=0:
      os.close(fdr)

def processAdapt(fns:FileNames,
                 code:str,
                 timeout:float=1.0)->Tuple[ReadResult,RunResult]:
  """ Push `code` to the interpreter and wait for `timeout` seconds for
  the immediate answer. In case of delay, return intermediate answer and
  the continuation context."""
  runr=processAsync(fns,code)
  rr=processCont(fns,runr,timeout=timeout)
  return rr,runr

PRESULT_RE=re.compile(r"(.*)\[BG:([a-zA-Z0-9_\/\.-]+)\]\n.*",
                      re.A|re.MULTILINE|re.DOTALL)

def rresultLoad(text:str)->Tuple[str,Optional[RunResult]]:
  m=re_match(PRESULT_RE,text)
  if m:
    return (m[1],RunResult(m[2],PATTERN))
  else:
    return text,None

def rresultSave(text:str, presult:RunResult)->str:
  return (text+f"\n[BG:{presult.fname}]\n"
          "<Re-evaluate to update>\n")

