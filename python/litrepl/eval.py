import re
import os
import sys
import fcntl

from copy import deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable
from re import search, match as re_match
from select import select
from os import environ, system
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter
from os.path import isfile
from signal import signal, SIGINT
from time import sleep
from dataclasses import dataclass
from functools import partial
from argparse import ArgumentParser

def pstderr(*args,**kwargs):
  print(*args, file=sys.stderr, **kwargs)

def mkre(prompt:str):
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
    if r==b'':
      return acc.decode('utf-8')
    # acc+=r
    acc,i_n=merge(acc,r,i_n)
    m=re_match(prompt,acc)
    if m:
      ans=m.group(1)
      return ans.decode('utf-8')
  return "LitREPL timeout waiting the interpreter response"

def readout_asis(fdr, fo, prompt, timeout:Optional[int]=None)->None:
  acc:bytes=b''
  while select([fdr],[],[],timeout)[0] != []:
    r=os.read(fdr, 1024)
    if r==b'':
      return
    fo.write(r)
    acc+=r # TODO: don't store everything
    m=re_match(prompt,acc)
    if m:
      return
  fo.write("LitREPL timeout waiting for the interpreter response\n")

PATTERN='3256748426384\n'

def interact(fdr, fdw, text:str, fo, pattern)->None:
  _m=merge_rn2
  os.write(fdw,pattern.encode())
  x=readout(fdr,prompt=mkre(pattern),merge=_m)
  os.write(fdw,text.encode())
  os.write(fdw,'\n'.encode())
  os.write(fdw,pattern.encode())
  readout_asis(fdr,fo,prompt=mkre(pattern))

@dataclass
class PResult:
  pid:int       # Code feed process
  fname:str     # Result file name
  pattern:str   # Shell stop patter

def perror(fname,err)->None:
  with open(fname,"w") as f:
    f.write(err)


def processAsync(lines:str)->PResult:
  codehash=abs(hash(lines))
  # fname=f"/tmp/litrepl-eval-{codehash}.txt"
  fname=f"/tmp/litrepl-eval-test.txt"
  pattern=PATTERN
  pid=os.fork()
  if pid==0:
    fdr=0; fdw=0
    try:
      fdw=os.open('_inp.pipe', os.O_WRONLY|os.O_SYNC)
      fdr=os.open('_out.pipe', os.O_RDONLY|os.O_SYNC)
      if fdw<0 or fdr<0:
        perror(fname,f"ERROR: litrepl.py couldn't open session pipes\n")
      fcntl.flock(fdw,fcntl.LOCK_EX|fcntl.LOCK_NB)
      fcntl.flock(fdr,fcntl.LOCK_EX|fcntl.LOCK_NB)
      with open(fname,"wb") as fo:
        interact(fdr,fdw,lines,fo,pattern)
    except BlockingIOError:
      perror(fname,"ERROR: litrepl.py couldn't lock the sessions pipes\n")
    finally:
      if fdr!=0:
        os.close(fdr)
      if fdw!=0:
        os.close(fdw)
    exit(0)
  else:
    return PResult(pid,fname,pattern)


def process(lines:str)->str:
  ipid=int(open('_pid.txt').read())
  r=processAsync(lines)
  def _handler(signum,frame):
    os.kill(r.ipid,SIGINT)
  fdr=0
  prev=signal(SIGINT,_handler)
  try:
    (pid,exitcode)=os.waitpid(r.pid,0)
    assert pid==r.pid
    fdr=os.open(r.fname,os.O_RDONLY|os.O_SYNC)
    return readout(fdr,prompt=mkre(r.pattern),merge=merge_rn2)
  finally:
    if prev is not None:
      signal(SIGINT,prev)
    if fdr!=0:
      os.close(fdr)

