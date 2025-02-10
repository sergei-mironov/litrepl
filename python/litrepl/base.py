import os
import sys
import fcntl
import re

from re import search, match as re_match, compile as re_compile
from copy import copy, deepcopy
from typing import (List, Optional, Tuple, Set, Dict, Callable, Any, Iterable,
                    Union)
from select import select
from os import (environ, system, isatty, getpid, unlink, getpgid, setpgid,
                mkfifo, kill)
from lark import Lark, Visitor, Transformer, Token, Tree, LarkError
from lark.visitors import Interpreter as LarkInterpreter
from os.path import isfile, join, exists, basename, splitext, dirname
from signal import signal, SIGINT, SIGKILL, SIGTERM
from time import sleep, time
from dataclasses import dataclass
from functools import partial
from argparse import ArgumentParser
from collections import defaultdict
from os import makedirs, getuid, getcwd, WEXITSTATUS, remove
from tempfile import gettempdir
from psutil import Process, NoSuchProcess
from textwrap import dedent
from subprocess import check_output, DEVNULL, CalledProcessError
from contextlib import contextmanager

from .types import (PrepInfo, RunResult, NSec, FileName, SecRec, FileNames,
                    CursorPos, ReadResult, SType, LitreplArgs, EvalState,
                    ECode, ECODE_OK, ECODE_RUNNING, SECVAR_RE, Interpreter,
                    LarkGrammar, Symbols, LarkTree, ParseResult, ErrorMsg)
from .eval import (process, pstderr, rresultLoad, rresultSave, processAdapt,
                   processCont, interpExitCode, readipid, with_parent_finally,
                   with_fd, read_nonblock, eval_code, eval_code_, interpIsRunning)
from .utils import(unindent, indent, escape, fillspaces, fmterror,
                   cursor_within, nlines, wraplong, remove_silent, hashdigest)

from .interpreters.python import PythonInterpreter
from .interpreters.ipython import IPythonInterpreter
from .interpreters.aicli import AicliInterpreter
from .interpreters.shell import ShellInterpreter

DEBUG:bool=False

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f},{getpid()}]", *args, file=sys.stderr, **kwargs, flush=True)

def st2auxdir(a:LitreplArgs, st:SType)->str:
  """ Return the aux.dir name for this section type """
  d,interp=None,None
  if st==SType.SPython:
    d,interp=a.python_auxdir,a.python_interpreter
  elif st==SType.SAI:
    d,interp=a.ai_auxdir,a.ai_interpreter
  elif st==SType.SShell:
    d,interp=a.sh_auxdir,a.sh_interpreter
  else:
    raise ValueError(f"Invalid section type {st}")
  if d is None:
    d = defauxdir(st)
  def _dotted(s):
    return f".{s}" if len(s)>0 else s
  for p,v in {
    '%%': '%',
    '%TD': gettempdir(),
    '%UI': str(getuid()),
    '%CH': hashdigest(getcwd()),
    '%IH': hashdigest(interp),
    '%FN': splitext(basename(environ.get('LITREPL_FILE','')))[0],
    '%FE': _dotted(splitext(basename(environ.get('LITREPL_FILE','')))[1]),
    '%FD': dirname(environ.get('LITREPL_FILE','')),
  }.items():
    d = d.replace(p,v)
  return d

def defauxdir(st:SType)->str:
  """ Calculate the default aux. directory name. """
  return join('%TD','litrepl_%UI_%CH',st2name(st))

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
  """ Return the background interpreter session state: input and output pipe
  names, pid, etc. If not explicitly specified in the config, the state is
  shared for all files in the current directory. """
  auxdir=st2auxdir(a,st)
  return FileNames(auxdir,
                   join(auxdir,"in.pipe"),join(auxdir,"out.pipe"),
                   join(auxdir,"pid.txt"),join(auxdir,"ecode.txt"),join(auxdir,"emsg.txt"))

def attach(fns:FileNames, st:Optional[SType]=None)->Union[Interpreter,ErrorMsg]:
  """ Attach to the interpreter associated with the given pipe filenames. """
  pid=readipid(fns)
  if pid is None:
    return f"Could not determine pid of an interpreter"
  try:
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
      return f"Unknown or undefined interpreter pid {pid} cmd '{cmd}' (among {st})"
    pdebug(f"Interpreter pid {pid} cmd '{cmd}' was resolved into '{cls}'")
    return cls(fns)
  except NoSuchProcess as err:
    return f"Could resolve pid {pid} into interpreter class: ({err})"

def open_child_pipes(inp,outp):
  return os.open(inp,os.O_RDWR|os.O_SYNC),os.open(outp,os.O_RDWR|os.O_SYNC);
def open_parent_pipes(inp,outp):
  return open(inp,'w'),open(outp,'r')


def write_child_pid(pidf,pid):
  """ Writes first children of a fork-child process as the main interpreter
  pid. This works as long as `Interpreter.run_child` calls real interpreter
  using system() call."""
  with open(pidf,'w') as f:
    for attempt in range(20):
      try:
        f.write(str(Process(pid).children()[0].pid))
        return True
      except IndexError:
        sleep(0.1)
  return False

def start_(a:LitreplArgs, interpreter:str, i:Interpreter, restart:bool)->int:
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `inp.pipe`, `out.pipe`, `pid.txt`, etc."""
  fns=i.fns
  if not restart and interpIsRunning(fns):
    pdebug(f"Not restarting an already running interpreter")
    return 2
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

def start(a:LitreplArgs, st:SType, restart:bool=False)->int:
  """ Start Litrepl session of type `st`. """
  if isdisabled(a,st):
    raise ValueError(f"Interpreter class {st2name(st)} is disabled by the user")
  fns=pipenames(a,st)
  if st is SType.SPython:
    if 'ipython' in a.python_interpreter.lower():
      return start_(a,a.python_interpreter,IPythonInterpreter(fns),restart)
    elif 'python' in a.python_interpreter:
      return start_(a,a.python_interpreter,PythonInterpreter(fns),restart)
    elif a.python_interpreter=='auto':
      if system('python3 -m IPython -c \'print("OK")\' >/dev/null 2>&1')==0:
        return start_(a,'python3 -m IPython',IPythonInterpreter(fns),restart)
      else:
        return start_(a,'python3',PythonInterpreter(fns),restart)
    else:
      raise ValueError(f"Unsupported python interpreter: {a.python_interpreter}")
  elif st is SType.SAI:
    assert not a.exception_exitcode, "--exception-exitcode is not compatible with `ai`"
    interpreter='aicli' if a.ai_interpreter=='auto' else a.ai_interpreter
    return start_(a,interpreter,AicliInterpreter(fns),restart)
  elif st is SType.SShell:
    assert not a.exception_exitcode, "--exception-exitcode is not compatible with `sh`"
    interpreter='/bin/sh' if a.sh_interpreter=='auto' else a.sh_interpreter
    return start_(a,interpreter,ShellInterpreter(fns),restart)
  else:
    raise ValueError(f"Unsupported section type: {st}")

def isdisabled(a:LitreplArgs, st:SType)->bool:
  return getattr(a,f"{st2name(st)}_interpreter",None)=='-'

def restart(a:LitreplArgs,st:SType):
  start(a,st,restart=True)

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
    self.codebegin = codebegin_re
    self.codeend="```"
    self.resultbegin=r"```[ ]*l?result|```[ ]*{[^}]*result[^}]*}"
    self.resultend="```"
    self.comcodebegin=comcodebegin_re
    self.comcodeend=comcodeend_re
    self.comresultbegin="<!--[ ]*l?result[ ]*-->"
    self.comresultend="<!--[ ]*l?noresult[ ]*-->"
    self.ignorebegin=r"<!--[ ]*l?ignore[ ]*-->"
    self.ignoreend=r"<!--[ ]*l?noignore[ ]*-->"
    self.secbegin_dict={
      'vim':(codebegin_re+'|'+comcodebegin_re).replace('?','\?'),
      'lark':(codebegin_re+'|'+comcodebegin_re)
    }
    self.secend_dict={
      'vim':(self.resultend+'|'+self.comresultend).replace('?','\?'),
      'lark':(self.resultend+'|'+self.comresultend),
    }

@dataclass
class SymbolsLatex(Symbols):
  def __init__(self, a:LitreplArgs):
    markers=[]
    for st in SType:
      markers.extend(a.markers[st])
    codebegin_vim_re='|'.join([r"\\begin\{[ ]*l\?"+m+r"\}" for m in markers])
    codebegin_lark_re='|'.join([r"\\begin\{[ ]*l?"+m+r"\}" for m in markers])
    codeend_re='|'.join([r"\\end\{l?"+m+r"\}" for m in markers])
    comcodebegin_vim_re='|'.join([fr"\%[ ]*l\?{m}" for m in markers])
    comcodebegin_lark_re='|'.join([fr"\%[ ]*l?{m}" for m in markers])
    comcodeend_re='|'.join([fr"\%[ ]*l?no{m}" for m in markers])
    resultend_vim_re=r"\\end\{l\?[a-zA-Z0-9]*result\}"
    resultend_lark_re=r"\\end\{l?[a-zA-Z0-9]*result\}"
    comresultend_vim_re=r"\%[ ]*l\?noresult"
    comresultend_lark_re=r"\%[ ]*l?noresult"
    self.codebegin=codebegin_lark_re
    self.codeend=codeend_re
    self.resultbegin=r"\\begin\{l?[a-zA-Z0-9]*result\}"
    self.resultend=resultend_lark_re
    self.comcodebegin=comcodebegin_lark_re
    self.comcodeend=comcodeend_re
    self.comresultbegin=r"\%[ ]*l?result"
    self.comresultend=comresultend_lark_re
    self.ignorebegin=r"\%[ ]*lignore|\%[ ]*l?ignore[ ]*\%"
    self.ignoreend=r"\%[ ]*lnoignore|\%[ ]*l?noignore[ ]*\%"
    self.inlinemarker=r"\\l[a-zA-Z0-9]*inline"
    self.secbegin_dict={
      'vim':codebegin_vim_re+'|'+comcodebegin_vim_re,
      'lark':codebegin_lark_re+'|'+comcodebegin_lark_re,
    }
    self.secend_dict={
      'vim':resultend_vim_re+'|'+comresultend_vim_re,
      'lark':resultend_lark_re+'|'+comresultend_lark_re,
    }

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

def parse_as(a,inp,filetype)->Union[ParseResult,LarkError]:
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

def parse_maybe(a:LitreplArgs)->Optional[ParseResult]:
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
      pdebug(f"parsing finish (None)")
      return None
    else:
      raise ers[0]
  res=sorted(prs,key=lambda pr:numcodesec(pr.tree))[-1]
  pdebug(f"parsing finish")
  return res

def parse_(a:LitreplArgs)->ParseResult:
  res=parse_maybe(a)
  if res is None:
    raise ValueError(f"Unsupported filetype \"{a.filetype}\"")
  return res

def failmsg(fns:FileNames,ss:Union[Interpreter,str],ec:ECode)->str:
  """ Retrieve information about the failed interpreter: attempt to access its
  last error message, format the syscall diagnostic, print OS exitcode. """
  msg=''
  try:
    with open(fns.emsgf) as f:
      msg+=f.read().rstrip()+"\n"
  except FileNotFoundError:
    pass
  if isinstance(ss,str):
    msg+=ss.rstrip()+"\n"
  else:
    if ec is not ECODE_RUNNING:
      msg+=f"Interpreter process terminated with OS exitcode: {ec}\n"
  msg+=f"Note: auxiliary directory is set to \"{fns.wd}\"\n"
  return msg

def eval_section_(a:LitreplArgs, tree:LarkTree, sr:SecRec, interrupt:bool=False)->ECode:
  """ Evaluate code sections of the parsed `tree`, as specified in the `sr`
  request.  """
  nsecs=sr.nsecs
  es=EvalState(sr)

  def _st2interp(st:SType)->Tuple[FileNames,Union[Interpreter,ErrorMsg]]:
    """ Resolve pipe filenames for the interpreter class `st`. """
    es.stypes.add(st)
    fns=pipenames(a,st)
    if not running(a,st):
      start(a,st)
    ss=attach(fns,st)
    if not isinstance(ss,Interpreter):
      return (fns,ss)
    if interrupt:
      ipid=readipid(fns)
      if ipid is not None:
        pdebug("Sending SIGINT to the interpreter")
        os.kill(ipid,SIGINT)
      else:
        pdebug("Failed to determine interpreter pid, not sending SIGINT")
    return fns,ss

  def _bm2interp(bmarker:str)->Tuple[Optional[FileNames],Union[Interpreter,ErrorMsg]]:
    """ Map code marker into FileName (None if the code marker is disabled by
    options) and resolve the interpreter. """
    st=bmarker2st(a,bmarker)
    if st is None:
      return (None, f"Failed to attach to interpreter.")
    return _st2interp(st)

  def _checkecode(fns,nsec,pending:bool)->ECode:
    ec=interpExitCode(fns)
    pdebug(f"Interpreter exit code: {ec}")
    if ec is ECODE_RUNNING:
      if pending and a.pending_exitcode:
        es.ecodes[nsec]=a.pending_exitcode
      else:
        es.ecodes[nsec]=ECODE_RUNNING
    else:
      es.ecodes[nsec]=ec
    return ec

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
        ok,sres,ec=False,'',ECODE_RUNNING
        fns,ss=_bm2interp(bmarker)
        if isinstance(fns,FileNames):
          rr=None
          if isinstance(ss,Interpreter):
            sres,rr=eval_code_(a,fns,ss,es,code,sr.preproc.pending.get(es.nsec))
          ec=_checkecode(fns,es.nsec,(rr.timeout if rr else False))
          if (ec is not ECODE_RUNNING) or isinstance(ss,str):
            msg=failmsg(fns,ss,ec)
            pstderr(msg)
            sres+=msg
          es.sres[es.nsec]=sres
        else:
          pass # The interpreter is disabled

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
        if isinstance(ss,Interpreter):
          result=process(a,fns,ss,'print('+code+');\n')[0].rstrip('\n')
        ec=_checkecode(fns,es.nsec,False)
        if ec is not ECODE_RUNNING:
          pusererror(failmsg(fns,ss,ec))
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
sloc : NUM ":" NUM -> s_cursor
     | const -> s_const
const : NUM -> s_const_num
      | "$" -> s_const_last
      | SIGN NUM -> s_const_rel
NUM : /[0-9]+/
SIGN : /[+-]/
"""

def solve_sloc(s:str, tree:LarkTree)->SecRec:
  """ Translate "sloc" string `s` into a `SecRec` processing request on the
  given parsed document `tree`. """
  p=Lark(grammar_sloc)
  t=p.parse(s)
  nknown:Dict[int,Callable[[int],int]]={}
  nqueries:Dict[int,CursorPos]={}
  # print(t.pretty())
  lastq=0
  last_cursor:Optional[CursorPos]=None
  class T(Transformer):
    def __init__(self)->None:
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
      nknown[self.q]=lambda _: int(tree[0].value)-1
      return int(self.q)
    def s_const_rel(self,tree):
      self.q+=1
      sign = 1 if tree[0].value == "+" else -1
      def _rel(ref):
        if ref is None:
          raise ValueError("A valid cursor position is required for relative addressing")
        return ref + sign * int(tree[1].value)
      nknown[self.q]=_rel
      return int(self.q)
    def s_const_last(self,tree):
      return int(lastq)
    def s_cursor(self,tree):
      nonlocal last_cursor
      self.q+=1
      last_cursor=(int(tree[0].value), int(tree[1].value))
      nqueries[self.q]=last_cursor
      return int(self.q)
  qs=T().transform(t)
  ppi=solve_cpos(tree,list(nqueries.values()))
  nsec,nsol=ppi.nsec,ppi.cursors
  nref:Optional[NSec]=nsol.get(last_cursor)
  nknown[lastq]=lambda _:nsec
  def _get(q):
    return nsol[nqueries[q]] if q in nqueries else nknown[q](nref)
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

def status(a:LitreplArgs, t:Optional[LarkTree], sts:List[SType], version):
  if a.verbose:
    return status_verbose(a,t,sts,version)
  else:
    return status_oneline(a,sts)

def status_oneline(a:LitreplArgs,sts:List[SType])->int:
  for st in sts:
    fns=pipenames(a,st)
    try:
      pid=open(fns.pidf).read().strip()
      cmd=' '.join(Process(int(pid)).cmdline())
    except Exception as ex:
      pdebug(f"exception: {ex}")
      pid='-'
      cmd='-'
    try:
      ecode=open(fns.ecodef).read().strip()
    except Exception:
      ecode='-'
    print(f"{st2name(st):6s} {pid:10s} {ecode:3s} {fns.wd} {cmd}")

def status_verbose(a:LitreplArgs, t:Optional[LarkTree], sts:List[SType], version:str)->int:
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
        assert isinstance(ss,Interpreter)
        interpreter_path=eval_code(a,fns,ss,es,
          '\n'.join(["import os","print(os.environ.get('PATH',''))"]))
        print(f"{st2name(st)} interpreter PATH: {interpreter_path.strip()}")
      except Exception:
        print(f"{st2name(st)} interpreter PATH: ?")
      try:
        assert isinstance(ss,Interpreter)
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
