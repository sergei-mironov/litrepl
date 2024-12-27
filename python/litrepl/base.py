import os
import sys
import fcntl
import re

from re import search, match as re_match, compile as re_compile
from copy import copy, deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable, Any, Iterable
from select import select
from os import (environ, system, isatty, getpid, unlink, getpgid, setpgid,
                mkfifo, kill)
from lark import Lark, Visitor, Transformer, Token, Tree, LarkError
from lark.visitors import Interpreter as LarkInterpreter
from os.path import isfile, join, exists
from signal import signal, SIGINT, SIGKILL, SIGTERM
from time import sleep, time
from dataclasses import dataclass
from functools import partial
from argparse import ArgumentParser
from collections import defaultdict
from os import makedirs, getuid, getcwd, WEXITSTATUS, remove
from tempfile import gettempdir
from hashlib import sha256
from psutil import Process, NoSuchProcess
from textwrap import dedent
from subprocess import check_output, DEVNULL, CalledProcessError
from contextlib import contextmanager

from .types import (PrepInfo, RunResult, NSec, FileName, SecRec, FileNames,
                    CursorPos, ReadResult, SType, LitreplArgs,
                    EvalState, ECode, ECODE_OK, ECODE_RUNNING, SECVAR_RE,
                    Interpreter, LarkGrammar, Symbols, LarkTree, ParseResult)
from .eval import (process, pstderr, rresultLoad, rresultSave, processAdapt,
                   processCont, interpExitCode, readipid, with_parent_finally,
                   with_fd, read_nonblock, eval_code, eval_code_)
from .utils import(unindent, indent, escape, fillspaces, fmterror,
                   cursor_within, nlines, wraplong, remove_silent)

from .interpreters.python import PythonInterpreter
from .interpreters.ipython import IPythonInterpreter
from .interpreters.aicli import AicliInterpreter
from .interpreters.shell import ShellInterpreter

DEBUG:bool=False

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f},{getpid()}]", *args, file=sys.stderr, **kwargs, flush=True)

def st2auxdir(a:LitreplArgs, st:SType, default=None)->str:
  """ Return the aux.dir name for this section type """
  d=None
  if st == SType.SPython:
    d=a.python_auxdir
  elif st==SType.SAI:
    d=a.ai_auxdir
  elif st==SType.SShell:
    d=a.sh_auxdir
  else:
    raise ValueError(f"Invalid section type {st}")
  return d or (default(st) if default else defauxdir(st))

def defauxdir(st:SType, suffix:Optional[str]=None)->str:
  """ Calculate the default aux. directory name. """
  suffix_=f"{suffix}_" if suffix is not None else ""
  return join(gettempdir(),
              (f"litrepl_{getuid()}_"+suffix_+
               sha256(getcwd().encode('utf-8')).hexdigest()[:6]),
              st2name(st))

def st2name(st:SType)->str:
  """ Return string representation of the code section type """
  if st==SType.SPython:
    return "python"
  elif st==SType.SAI:
    return "ai"
  elif st==SType.SShell:
    return "sh"
  else:
    raise ValueError(f"Invalid interpreter class: {st}")

def name2st(name:str)->SType:
  if name=="python":
    return SType.SPython
  elif name=="ai":
    return SType.SAI
  elif name=="sh":
    return SType.SShell
  else:
    raise ValueError(f"Invalid interpreter class name: {name}")

def bmarker2st(a:LitreplArgs, bmarker:str)->Optional[SType]:
  """ Maps section code marker to section type """
  acc=[]
  for st in SType:
    if not isdisabled(a,st):
      bms=a.markers[st]
      if any((bm in bmarker) for bm in bms):
        acc.append(st)
  if len(acc)==1:
    return acc[0]
  else:
    if len(acc)==0:
      return None
    else:
      raise ValueError(
        f"Marker \"{bmarker}\" matches more than one interpreter class: "+
        ', '.join([f'"{st2name(c)}"' for c in acc])
      )

def pipenames(a:LitreplArgs, st:SType)->FileNames:
  """ Return the interpreter state: input and output pipe names, pid, etc. If
  not explicitly specified in the config, the state is shared for all files in
  the current directory. """
  auxdir=st2auxdir(a,st)
  return FileNames(auxdir,
                   join(auxdir,"_in.pipe"),join(auxdir,"_out.pipe"),
                   join(auxdir,"_pid.txt"),join(auxdir,"_ecode.txt"),join(auxdir,"_emsg.txt"))

def attach(fns:FileNames, st:SType|None=None)->Optional[Interpreter]:
  """ Attach to the interpreter associated with the given pipe filenames. """
  try:
    pid=readipid(fns)
    if pid is None:
      pdebug(f"Could not determine pid of an interpreter")
      return None
    p=Process(pid)
    cmd=p.cmdline()
    cls=None
    if (st is None or st==SType.SAI) and any('aicli' in w for w in cmd):
      cls=AicliInterpreter
    elif (st is None or st==SType.SPython) and any('ipython' in w for w in cmd):
      cls=IPythonInterpreter
    elif (st is None or st==SType.SPython) and any('python' in w for w in cmd):
      cls=PythonInterpreter
    elif (st is None or st==SType.SShell) and any('sh' in w for w in cmd):
      cls=ShellInterpreter
    else:
      assert False, f"Unknown or undefined interpreter {cmd} (among {st})"
    pdebug(f"Interpreter pid {pid} cmd '{cmd}' was resolved into '{cls}'")
    return cls(fns)
  except NoSuchProcess as p:
    pdebug(f"Could not determine the interpreter classs for ({p})")
    return None

def open_child_pipes(inp,outp):
  return os.open(inp,os.O_RDWR|os.O_SYNC),os.open(outp,os.O_RDWR|os.O_SYNC);
def open_parent_pipes(inp,outp):
  return open(inp,'w'),open(outp,'r')


def write_child_pid(pidf,pid):
  with open(pidf,'w') as f:
    for attempt in range(20):
      try:
        f.write(str(Process(pid).children()[0].pid))
        return True
      except IndexError:
        sleep(0.1)
  return False

def start_(a:LitreplArgs, interpreter:str, i:Interpreter)->int:
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `_inp.pipe`, `_out.pipe`, `_pid.txt`, etc."""
  fns=i.fns
  makedirs(fns.wd, exist_ok=True)
  try:
    with open(fns.pidf,'r') as pid_file:
      kill(int(pid_file.read().strip()), SIGKILL)
  except (ValueError,FileNotFoundError,ProcessLookupError):
    pass
  remove_silent(fns.inp)
  remove_silent(fns.outp)
  mkfifo(fns.inp)
  mkfifo(fns.outp)
  sys.stdout.flush(); sys.stderr.flush() # FIXME: to avoid duplicated stdout
  npid=os.fork()
  if npid==0:
    # sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    setpgid(getpid(),0)
    remove_silent(fns.ecodef)
    open_child_pipes(fns.inp,fns.outp)
    ret=i.run_child(interpreter)
    ret=ret if ret<256 else WEXITSTATUS(ret)
    with open(fns.emsgf,'w') as f:
      f.write(read_nonblock(fns.outp))
    pdebug(f"Fork records ecode: {ret} into {fns.wd}")
    with open(fns.ecodef,'w') as f:
      f.write(str(ret))
    exit(ret)
  else:
    finp,foutp=open_parent_pipes(fns.inp,fns.outp)
    i.setup_child(a,finp,foutp)
    if write_child_pid(fns.pidf,npid):
      return 0
    else:
      return 1

def start(a:LitreplArgs, st:SType)->int:
  if isdisabled(a,st):
    raise ValueError(f"Interpreter class {st2name(st)} is disabled by the user")
  fns=pipenames(a,st)
  if st is SType.SPython:
    if 'ipython' in a.python_interpreter.lower():
      return start_(a,a.python_interpreter,IPythonInterpreter(fns))
    elif 'python' in a.python_interpreter:
      return start_(a,a.python_interpreter,PythonInterpreter(fns))
    elif a.python_interpreter=='auto':
      if system('python3 -m IPython -c \'print("OK")\' >/dev/null 2>&1')==0:
        return start_(a,'python3 -m IPython',IPythonInterpreter(fns))
      else:
        return start_(a,'python3',PythonInterpreter(fns))
    else:
      raise ValueError(f"Unsupported python interpreter: {a.python_interpreter}")
  elif st is SType.SAI:
    assert not a.exception_exitcode, "Not supported"
    interpreter='aicli' if a.ai_interpreter=='auto' else a.ai_interpreter
    return start_(a,interpreter,AicliInterpreter(fns))
  elif st is SType.SShell:
    assert not a.exception_exitcode, "Not supported"
    interpreter='/bin/sh' if a.sh_interpreter=='auto' else a.sh_interpreter
    return start_(a,interpreter,ShellInterpreter(fns))
  else:
    raise ValueError(f"Unsupported section type: {st}")

def isdisabled(a:LitreplArgs, st:SType)->bool:
  return getattr(a,f"{st2name(st)}_interpreter",None)=='-'

def restart(a:LitreplArgs,st:SType):
  stop(a,st); start(a,st)

def running(a:LitreplArgs,st:SType)->bool:
  """ Checks if the background session was run or not. """
  fns = pipenames(a,st)
  return (isfile(fns.pidf) and exists(fns.inp) and exists(fns.outp))

def stop(a:LitreplArgs,st:SType)->None:
  """ Stops the background interpreter session. """
  fns = pipenames(a,st)
  try:
    with open(fns.pidf, 'r') as pid_file:
      kill(int(pid_file.read().strip()),SIGTERM)
  except (FileNotFoundError,ValueError,ProcessLookupError):
    pass
  remove_silent(fns.pidf)
  remove_silent(fns.inp)

@dataclass
class SymbolsMarkdown(Symbols):
  def __init__(self, a:LitreplArgs):
    markers=[]
    for st in SType:
      markers.extend(a.markers[st])
    codebegin_re='|'.join(
      [fr"```[ ]*l?{m}" for m in markers]+
      [r"```[ ]*{[^}]*"+m+r"[^}]*}" for m in markers]
    )
    comcodebegin_re='|'.join([fr"<!--[ ]*l?{m}[ ]*-->" for m in markers])
    comcodeend_re='|'.join([fr"<!--[ ]*l?no{m}[ ]*-->" for m in markers])
    self.codebegin_dict = {
      'vim': codebegin_re,
      'lark': codebegin_re
    }
    self.codebegin = self.codebegin_dict['lark']
    self.codeend = "```"
    self.resultbegin = r"```[ ]*l?result|```[ ]*{[^}]*result[^}]*}"
    self.resultend = "```"
    self.comcodebegin = comcodebegin_re
    self.comcodeend = comcodeend_re
    self.comresultbegin = "<!--[ ]*l?result[ ]*-->"
    self.comresultend = "<!--[ ]*l?noresult[ ]*-->"
    self.ignorebegin = r"<!--[ ]*l?ignore[ ]*-->"
    self.ignoreend = r"<!--[ ]*l?noignore[ ]*-->"

@dataclass
class SymbolsLatex(Symbols):
  def __init__(self, a:LitreplArgs):
    markers=[]
    for st in SType:
      markers.extend(getattr(a,f"{st2name(st)}_markers").split(","))
    codebegin_vim_re='|'.join([r"\\begin\{[ ]*l\?"+m+r"\}" for m in markers])
    codebegin_lark_re='|'.join([r"\\begin\{[ ]*l?"+m+r"\}" for m in markers])
    codeend_re='|'.join([r"\\end\{l?"+m+r"\}" for m in markers])
    comcodebegin_re='|'.join([fr"\%[ ]*l?{m}" for m in markers])
    comcodeend_re='|'.join([fr"\%[ ]*l?no{m}" for m in markers])

    self.codebegin_dict = {
      'vim': codebegin_vim_re,
      'lark': codebegin_lark_re
    }
    self.codebegin = self.codebegin_dict['lark']
    self.codeend = codeend_re
    self.resultbegin = r"\\begin\{l?[a-zA-Z0-9]*result\}"
    self.resultend = r"\\end\{l?[a-zA-Z0-9]*result\}"
    self.comcodebegin = comcodebegin_re
    self.comcodeend = comcodeend_re
    self.comresultbegin = r"\%[ ]*l?result"
    self.comresultend = r"\%[ ]*l?noresult"
    self.ignorebegin = r"\%lignore"
    self.ignoreend = r"\%lnoignore"
    self.inlinemarker = r"\\l[a-zA-Z0-9]*inline"

OBR="{"
CBR="}"
BCBR="\\}"
BOBR="\\{"

def grammar_(a:LitreplArgs, filetype:str)->Tuple[LarkGrammar,Symbols]:
  # For the `?!` syntax, see
  # https://stackoverflow.com/questions/56098140/how-to-exclude-certain-possibilities-from-a-regular-expression
  if filetype in ["md","markdown"]:
    symbols_md=SymbolsMarkdown(a)
    sl=symbols_md
    toplevel_markers_markdown='|'.join([
      sl.codebegin,sl.resultbegin,
      sl.comresultbegin, sl.ignorebegin, sl.comcodebegin
    ])
    return (dedent(fr"""
      start: (topleveltext)? (snippet (topleveltext)?)*
      snippet : codesec -> e_icodesection
              | resultsec -> e_ocodesection
              | ignoresec -> e_comsection
      ignoresec.2 : ignorebegin ignoretext ignoreend
      codesec.1 : codebegin codetext codeend
                     | comcodebegin codesectext comcodeend
      resultsec.1 : resultbegin resulttext resultend
                     | comresultbegin vertext comresultend
      codebegin : /{symbols_md.codebegin}/
      codeend : /{symbols_md.codeend}/
      comcodebegin : /{symbols_md.comcodebegin}/
      comcodeend : /{symbols_md.comcodeend}/
      resultbegin : /{symbols_md.resultbegin}/
      resultend : /{symbols_md.resultend}/
      comresultbegin : /{symbols_md.comresultbegin}/
      comresultend : /{symbols_md.comresultend}/
      inlinebeginmarker : "`"
      inlinendmarker : "`"
      ignorebegin : /{symbols_md.ignorebegin}/
      ignoreend : /{symbols_md.ignoreend}/
      topleveltext : /(.(?!{toplevel_markers_markdown}))*./s
      codetext : /(.(?!{symbols_md.codeend}))*./s
      resulttext : /(.(?!{symbols_md.resultend}))*./s
      ignoretext : /(.(?!{symbols_md.ignoreend}))*./s
      vertext : /(.(?!{symbols_md.comresultend}))*./s
      codesectext : /(.(?!{symbols_md.comcodeend}))*./s
      """), symbols_md)
  elif filetype in ["tex","latex"]:
    symbols_latex=SymbolsLatex(a)
    sl=symbols_latex
    toplevel_markers_latex='|'.join([
      sl.codebegin,sl.codeend,sl.comcodebegin,sl.comcodeend,
      sl.resultbegin,sl.resultend,sl.comresultbegin,sl.comresultend,
      sl.ignorebegin,sl.ignoreend,sl.inlinemarker+BOBR
    ])
    return (dedent(fr"""
      start: (topleveltext)? (snippet (topleveltext)? )*
      snippet : codesec -> e_icodesection
              | resultsec -> e_ocodesection
              | inlinecodesec -> e_inline
              | ignoresec -> e_comment
      ignoresec.2 : ignorebegin ignoretext ignoreend
      codesec.1 : codebegin codetext codeend
                | comcodebegin comcodetext comcodeend
      resultsec.1 : resultbegin resulttext resultend
                  | comresultbegin comresulttext comresultend
      inlinecodesec.1 : inlinemarker "{OBR}" inltext "{CBR}" spaces obr inltext cbr
      inlinemarker : /{symbols_latex.inlinemarker}/
      codebegin : /{symbols_latex.codebegin}/
      codeend : /{symbols_latex.codeend}/
      comcodebegin : /{symbols_latex.comcodebegin}/
      comcodeend : /{symbols_latex.comcodeend}/
      resultbegin : /{symbols_latex.resultbegin}/
      resultend : /{symbols_latex.resultend}/
      comresultbegin : /{symbols_latex.comresultbegin}/
      comresultend : /{symbols_latex.comresultend}/
      ignorebegin : /{symbols_latex.ignorebegin}/
      ignoreend : /{symbols_latex.ignoreend}/
      topleveltext : /(.(?!{toplevel_markers_latex}))*./s
      comcodetext : /(.(?!{symbols_latex.comcodeend}))*./s
      codetext : /(.(?!{symbols_latex.codeend}))*./s
      resulttext : /(.(?!{symbols_latex.resultend}))*./s
      comresulttext : /(.(?!{symbols_latex.comresultend}))*./s
      inltext : ( /[^{OBR}{CBR}]+({OBR}[^{CBR}]*{CBR}[^{OBR}{CBR}]*)*/ )?
      ignoretext : ( /(.(?!{symbols_latex.ignoreend}))*./s )?
      spaces : ( /[ \t\r\n]+/s )?
      obr : "{OBR}"
      cbr : "{CBR}"
      """), symbols_latex)
  else:
    raise ValueError(f"Unsupported filetype \"{filetype}\"")

def readinput(tty_ok=True)->str:
  return sys.stdin.read() if (not isatty(sys.stdin.fileno()) or tty_ok) else ""

def parse_as(a,inp,filetype)->ParseResult|LarkError:
  try:
    g,s=grammar_(a,filetype)
    parser=Lark(g,propagate_positions=True)
    tree=parser.parse(inp)
    return ParseResult(g,s,tree,filetype)
  except LarkError as e:
    return e

def numcodesec(tree:LarkTree)->int:
  class C(LarkInterpreter):
    def __init__(self):
      self.n=0
    def codesec(self,tree):
      self.n+=1
    def inlinecodesec(self,tree):
      self.n+=1
  c=C()
  c.visit(tree)
  return c.n

def parse_(a:LitreplArgs)->ParseResult:
  pdebug(f"parsing start")
  inp=readinput(a.tty)
  rs=[]
  if a.filetype in ['auto','tex','latex']:
    rs.append(parse_as(a,inp,'latex'))
  if a.filetype in ['auto','md','markdown']:
    rs.append(parse_as(a,inp,'markdown'))
  prs=[r for r in rs if isinstance(r,ParseResult)]
  if len(prs)==0:
    ers=[r for r in rs if isinstance(r,LarkError)]
    if len(ers)==0:
      raise ValueError(f"Unsupported filetype \"{a.filetype}\"")
    else:
      raise ers[0]
  res=sorted(prs,key=lambda pr:numcodesec(pr.tree))[-1]
  pdebug(f"parsing finish")
  return res

def eval_section_(a:LitreplArgs, tree:LarkTree, sr:SecRec, interrupt:bool=False)->ECode:
  """ Evaluate code sections of the parsed `tree`, as specified in the `sr`
  request.  """
  nsecs=sr.nsecs
  es=EvalState(sr)

  def _st2interp(st)->Tuple[Optional[FileNames],Optional[Interpreter]]:
    es.stypes.add(st)
    fns=pipenames(a,st)
    if not running(a,st):
      start(a,st)
    ss=attach(fns,st)
    if not ss:
      return (fns,None)
    if interrupt:
      ipid=readipid(fns)
      if ipid is not None:
        pdebug("Sending SIGINT to the interpreter")
        os.kill(ipid,SIGINT)
      else:
        pdebug("Failed to determine interpreter pid, not sending SIGINT")
    return fns,ss

  def _bm2interp(bmarker:str)->Tuple[Optional[FileNames],Optional[Interpreter]]:
    st=bmarker2st(a,bmarker)
    if st is None:
      return (None, None)
    return _st2interp(st)

  def _checkecode(fns,nsec,pending:bool)->ECode:
    ec=interpExitCode(fns)
    pdebug(f"interpreter exit code: {ec}")
    if ec is ECODE_RUNNING:
      if pending and a.pending_exitcode:
        es.ecodes[nsec]=a.pending_exitcode
      else:
        es.ecodes[nsec]=ECODE_RUNNING
    else:
      es.ecodes[nsec]=ec
    return ec

  def _failmsg(fns,ec):
    msg=''
    try:
      with open(fns.emsgf) as f:
        msg=f.read()
    except FileNotFoundError:
      pass
    if not msg.endswith('\n'):
      msg+='\n'
    return msg+f"<Interpreter exited with code: {ec}>\n"

  class C(LarkInterpreter):
    def _print(self, s:str):
      print(s, end='')
    def text(self,tree):
      self._print(tree.children[0].value)
    def topleveltext(self,tree):
      return self.text(tree)
    def codesec(self,tree):
      es.nsec+=1
      bmarker=tree.children[0].children[0].value
      t=tree.children[1].children[0].value
      emarker=tree.children[2].children[0].value
      self._print(f"{bmarker}{t}{emarker}")
      bm,em=tree.children[0].meta,tree.children[2].meta
      code=unindent(bm.column-1,t)
      if es.nsec in nsecs:
        fns,ss=_bm2interp(bmarker)
        if fns:
          rr=None
          if ss:
            es.sres[es.nsec],rr=eval_code_(a,fns,ss,es,code,sr.preproc.pending.get(es.nsec))
          ec=_checkecode(fns,es.nsec,rr.timeout if rr else False)
          if ec is not None:
            msg=_failmsg(fns,ec)
            pstderr(msg)
            es.sres[es.nsec]=es.sres.get(es.nsec,'')+msg
    def resultsec(self,tree):
      bmarker=tree.children[0].children[0].value
      t=tree.children[1].children[0].value
      emarker=tree.children[2].children[0].value
      bm,em=tree.children[0].meta,tree.children[2].meta
      if (es.nsec in nsecs) and (es.nsec in es.sres):
        t2="\n"+indent(bm.column-1,escape(es.sres[es.nsec],emarker))
        es.ledder[bm.line]=nlines(t2)-nlines(t)
        self._print(bmarker+t2+emarker)
        if a.irreproducible_exitcode and t!=t2:
          pstderr(f"Result mismatch:\nExisting:\n{t}\nNew:\n{t2}")
          es.ecodes[es.nsec]=a.irreproducible_exitcode
      else:
        self._print(f"{bmarker}{t}{emarker}")
    def inlinecodesec(self,tree):
      # FIXME: Latex-only
      bm,em=tree.children[0].meta,tree.children[4].meta
      code=tree.children[1].children[0].value
      spaces=tree.children[2].children[0].value if tree.children[2].children else ''
      im=tree.children[0].children[0].value
      if es.nsec in nsecs:
        fns,ss=_st2interp(SType.SPython)
        if fns:
          if ss:
            result=process(a,fns,ss,'print('+code+');\n')[0].rstrip('\n')
          ec=_checkecode(fns,es.nsec,False)
          if ec is not None:
            pusererror(_failmsg(fns,ec))
      else:
        result=tree.children[4].children[0].value if tree.children[4].children else ''
      self._print(f"{im}{OBR}{code}{CBR}{spaces}{OBR}{result}{CBR}")
    def ignoresec(self,tree):
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      self._print(f"{bmarker}{tree.children[1].children[0].value}{emarker}")

  def _finally():
    if a.map_cursor:
      cl=a.map_cursor[0] # cursor line
      for line,diff in sorted(es.ledder.items()):
        if cl>line:
          cl=max(line+1,cl+diff)
      with open(a.map_cursor_output,"w") as f:
        f.write(str(cl))
    if a.foreground:
      for st in es.stypes:
        stop(a,st)

  with with_parent_finally(_finally):
    C().visit(tree)

  ec=max(map(lambda x:ECODE_OK if x is None else x,
                 es.ecodes.values()),default=ECODE_OK)
  pdebug(f"eval_code_ ecodes {es.ecodes} => {ec}")
  return ec

def solve_cpos(tree, cs:List[CursorPos])->PrepInfo:
  """ Preprocess the document tree. Resolve the list of cursor locations `cs`
  into code section numbers. """
  cursors:dict={}
  rres:Dict[NSec,Set[RunResult]]=defaultdict(set)
  results:Dict[NSec,str]={}
  class C(LarkInterpreter):
    def __init__(self):
      self.nsec=-1
    def _count(self,bm,em):
      for (line,col) in cs:
        if cursor_within((line,col),(bm.line,bm.column),
                                    (em.end_line,em.end_column)):
          cursors[(line,col)]=self.nsec
    def _getrr(self,text,column):
      text1,pend=rresultLoad(text)
      results[self.nsec]=unindent(column,text1)
      if pend is not None:
        rres[self.nsec].add(pend)
    def codesec(self,tree):
      self.nsec+=1
      self._count(tree.children[0].meta,tree.children[2].meta)
    def resultsec(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
      contents=tree.children[1].children[0].value
      bm,em=tree.children[0].meta,tree.children[2].meta
      self._getrr(contents,bm.column-1)
    def oversection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
      self._getrr(tree.children[1].children[0].value)
    def inlinecodesec(self,tree):
      self._count(tree.children[0].meta,tree.children[5].meta)
  c=C()
  c.visit(tree)
  rres2:dict={}
  for k,v in rres.items():
    assert len(v)==1, f"Results of codesec #{k} refer to different readout files: ({list(v)})"
    rres2[k]=list(v)[0]
  return PrepInfo(c.nsec,cursors,rres2,results)

grammar_sloc = fr"""
start: addr -> l_const
     | addr (","|";") start -> l_add
addr : sloc ".." sloc -> a_range
     | sloc -> a_const
sloc : num ":" num -> s_cursor
     | const -> s_const
const : num -> s_const_num
      | "$" -> s_const_last
num : /[0-9]+/
"""

def solve_sloc(s:str, tree:LarkTree)->SecRec:
  """ Translate "sloc" string `s` into a `SecRec` processing request on the
  given parsed document `tree`. """
  p=Lark(grammar_sloc)
  t=p.parse(s)
  nknown:Dict[int,int]={}
  nqueries:Dict[int,CursorPos]={}
  # print(t.pretty())
  lastq=0
  class T(Transformer):
    def __init__(self):
      self.q=lastq
    def l_const(self,tree):
      return [tree[0]]
    def l_add(self,tree):
      return [tree[0]]+tree[1]
    def a_range(self,tree):
      return (tree[0],tree[1])
    def a_const(self,tree):
      return (tree[0],)
    def s_const(self,tree):
      return tree[0]
    def s_const_num(self,tree):
      self.q+=1
      nknown[self.q]=int(tree[0].children[0].value)
      return int(self.q)
    def s_const_last(self,tree):
      return int(lastq)
    def s_cursor(self,tree):
      self.q+=1
      nqueries[self.q]=(int(tree[0].children[0].value),
                        int(tree[1].children[0].value))
      return int(self.q)
  qs=T().transform(t)
  ppi=solve_cpos(tree,list(nqueries.values()))
  nsec,nsol=ppi.nsec,ppi.cursors
  nknown[lastq]=nsec
  def _get(q):
    return nsol[nqueries[q]] if q in nqueries else nknown[q]
  def _safeset(x):
    try:
      return set(x())
    except KeyError as err:
      pstderr(f"Unable to resolve section at {err}")
      return set()
  return SecRec(
    set.union(*[_safeset(lambda:range(_get(q[0]),_get(q[1])+1)) if len(q)==2
                else _safeset(lambda:[_get(q[0])]) for q in qs]),
    ppi)

def status(a:LitreplArgs, t:LarkTree|None, sts:List[SType], version):
  if a.verbose:
    return status_verbose(a,t,sts,version)
  else:
    return status_oneline(a,sts)

def status_oneline(a:LitreplArgs,sts:List[SType])->int:
  for st in sts:
    fns = pipenames(a, st)
    pdebug(f"status auxdir: {fns.wd}")
    try:
      pid = open(fns.pidf).read().strip()
      cmd = ' '.join(Process(int(pid)).cmdline())
    except Exception as ex:
      pdebug(f"exception: {ex}")
      pid = '-'
      cmd = '-'
    try:
      ecode = open(fns.ecodef).read().strip()
    except Exception:
      ecode = '-'
    print(f"{st2name(st):6s} {pid:10s} {ecode:3s} {cmd}")

def status_verbose(a:LitreplArgs, t:LarkTree|None, sts:List[SType], version:str)->int:
  sr=solve_sloc('0..$',t) if t is not None else None
  print(f"version: {version}")
  print(f"workdir: {getcwd()}")
  print(f"litrepl PATH: {environ.get('PATH','')}")
  ecodes=set()
  for st in sts:
    fns=pipenames(a, st)
    print(f"{st2name(st)} interpreter auxdir: {fns.wd}")
    try:
      pid=open(fns.pidf).read().strip()
      print(f"{st2name(st)} interpreter pid: {pid}")
    except Exception:
      print(f"{st2name(st)} interpreter pid: ?")
    if sr is not None:
      for nsec,pend in sr.preproc.pending.items():
        fname=pend.fname
        print(f"{st2name(st)} pending section {nsec} buffer: {fname}")
        try:
          for bline in check_output(['lsof','-t',fname],stderr=DEVNULL).split(b'\n'):
            line=bline.decode('utf-8')
            if len(line)==0:
              continue
            print(f"{st2name(st)} pending section {nsec} reader: {line}")
        except CalledProcessError:
          print(f"{st2name(st)} pending section {nsec} reader: ?")
    if st==SType.SPython:
      ss=attach(fns,st)
      es=EvalState(SecRec.empty())
      try:
        assert ss is not None
        interpreter_path=eval_code(a,fns,ss,es,
          '\n'.join(["import os","print(os.environ.get('PATH',''))"]))
        print(f"{st2name(st)} interpreter PATH: {interpreter_path.strip()}")
      except Exception:
        print(f"{st2name(st)} interpreter PATH: ?")
      try:
        assert ss is not None
        interpreter_pythonpath=eval_code(a,fns,ss,es,
          '\n'.join(["import sys","print(':'.join(sys.path))"]))
        print(f"{st2name(st)} interpreter PYTHONPATH: {interpreter_pythonpath.strip()}")
      except Exception:
        print(f"{st2name(st)} interpreter PYTHONPATH: ?")
    elif st==SType.SAI:
      pass
    elif st==SType.SShell:
      pass
    else:
      raise NotImplementedError(f'Unsupported type {st}')
    ecode=interpExitCode(fns)
    ecodes.add(0 if ecode is None else ecode)
  return max(ecodes)
