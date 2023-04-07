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
from time import sleep
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
    print(*args, file=sys.stderr, **kwargs, flush=True)

def mkre(prompt:str):
  """ Create the regexp that matches everything ending with a `prompt` """
  return re.compile(f"(.*)(?={prompt})|{prompt}".encode('utf-8'),
                    re.A|re.MULTILINE|re.DOTALL)

def merge_basic2(acc,r,xxx)->Tuple[bytes,int]:
  return (acc+r,xxx)

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

def readout_asis(fdr:int, fo:int, prompt, timeout:Optional[int]=None)->None:
  """ Read everything from FD `fdr` until `prompt` is found. Write everything to
  FD `fo`. """
  acc:bytes=b''
  while select([fdr],[],[],timeout)[0] != []:
    r=os.read(fdr, 1024)
    if r==b'':
      return
    w=os.write(fo,r)
    assert w==len(r), "LitREPL failed to copy input stream"
    acc+=r # TODO: don't store everything
    m=re_match(prompt,acc)
    if m:
      return
  os.write(fo,"<LitREPL: timeout waiting for the interpreter response>\n".encode())

PATTERN='3256748426384\n'

def interact(fdr, fdw, text:str, fo:int, pattern)->None:
  os.write(fdw,pattern.encode())
  x=readout(fdr,prompt=mkre(pattern),merge=merge_rn2)
  os.write(fdw,text.encode())
  os.write(fdw,'\n'.encode())
  os.write(fdw,pattern.encode())
  readout_asis(fdr,fo,prompt=mkre(pattern))

def pusererror(fname,err)->None:
  with open(fname,"w") as f:
    f.write(err)

def processAsync(fns:FileNames, lines:str)->RunResult:
  """ Send `lines` to the interpreter and fork the response reader """
  wd,inp,outp,pidf=astuple(fns)
  codehash=abs(hash(lines))
  fname=join(wd,f"litrepl_eval_{codehash}.txt")
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
      fdw=os.open(inp, os.O_WRONLY|os.O_SYNC)
      fdr=os.open(outp, os.O_RDONLY|os.O_SYNC)
      if fdw<0 or fdr<0:
        pusererror(fname,f"ERROR: litrepl.py couldn't open session pipes\n")
      fcntl.flock(fdw,fcntl.LOCK_EX|fcntl.LOCK_NB)
      fcntl.flock(fdr,fcntl.LOCK_EX|fcntl.LOCK_NB)
      def _handler(signum,frame):
        pass
      signal(SIGINT,_handler)
      interact(fdr,fdw,lines,fo,pattern)
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
    pdebug(f"Forked reader {pid}")
    fcntl.fcntl(fo,fcntl.LOCK_UN)
    os.close(fo)
    return RunResult(fname,pattern)

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


def process(fns:FileNames, lines:str)->str:
  """ Evaluate `lines` synchronously. """
  r=processAsync(fns, lines)
  fdr=0
  try:
    with with_sigint(fns):
      fdr=os.open(r.fname,os.O_RDONLY|os.O_SYNC)
      assert fdr>0
      fcntl.flock(fdr,LOCK_EX)
      res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
      return res
  finally:
    if fdr!=0:
      os.close(fdr)

def processCont(fns:FileNames, r:RunResult, timeout:float=1.0)->ReadResult:
  """ Continue reading from the already running readout process"""
  fdr=0
  rr:ReadResult
  try:
    with with_sigint(fns):
      fdr=os.open(r.fname,os.O_RDONLY|os.O_SYNC)
      assert fdr>0
      try:
        with with_alarm(timeout):
          fcntl.flock(fdr,LOCK_EX|(0 if timeout>0 else LOCK_NB))
        res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
        rr=ReadResult(res,False)
        os.unlink(r.fname)
        pdebug(f"processCont unlinked {r.fname}")
      except (BlockingIOError,TimeoutError):
        pdebug("processCont receieved Timeout or BlockingIOError")
        res=readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
        rr=ReadResult(res,True)
      return rr
  finally:
    if fdr!=0:
      os.close(fdr)

def processAdapt(fns:FileNames,
                 lines:str,
                 timeout:float=1.0)->Tuple[ReadResult,RunResult]:
  """ Push `lines` to the interpreter and wait for `timeout` seconds for
  immediate answer. In case of delay, return intermediate answer with
  the continuation."""
  runr=processAsync(fns,lines)
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

