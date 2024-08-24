import os
import sys
import fcntl
import re

from re import search, match as re_match, compile as re_compile
from copy import copy, deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable, Any, Iterable
from select import select
from os import environ, system, isatty, getpid, unlink, getpgid, setpgid
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter as LarkInterpreter
from os.path import isfile, join
from signal import signal, SIGINT
from time import sleep, time
from dataclasses import dataclass, astuple
from functools import partial
from argparse import ArgumentParser
from collections import defaultdict
from os import makedirs, getuid, getcwd, WEXITSTATUS
from tempfile import gettempdir
from hashlib import sha256
from psutil import Process, NoSuchProcess
from textwrap import dedent
from subprocess import check_output, DEVNULL, CalledProcessError
from contextlib import contextmanager

from .types import (PrepInfo, RunResult, NSec, FileName, SecRec, FileNames,
                    CursorPos, ReadResult, SType, LitreplArgs,
                    EvalState, ECode, ECODE_OK, ECODE_RUNNING, SECVAR_RE,
                    Interpreter)
from .eval import (process, pstderr, rresultLoad, rresultSave, processAdapt,
                   processCont, interpExitCode, readipid, with_parent_finally)
from .utils import(unindent, indent, escape, fillspaces, fmterror,
                   cursor_within, nlines, wraplong, blind_unlink)

DEBUG:bool=False

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f},{getpid()}]", *args, file=sys.stderr, **kwargs, flush=True)


def defauxdir(suffix:Optional[str]=None)->str:
  """ Generate the default name of working directory. """
  suffix_=f"{suffix}_" if suffix is not None else ""
  return join(gettempdir(),f"litrepl_{getuid()}_"+suffix_+
              sha256(getcwd().encode('utf-8')).hexdigest()[:6])

def st2name(st:SType)->str:
  if st==SType.SPython:
    return "python"
  elif st==SType.SAI:
    return "ai"
  else:
    raise ValueError(f"Invalid section type: {st}")

def name2st(name:str)->SType:
  if name=="python":
    return SType.SPython
  elif name=="ai":
    return SType.SAI
  else:
    raise ValueError(f"Invalid section name: {name}")

def bmarker2st(bmarker:str)->SType:
  """ Maps section code marker to section type """
  if 'ai' in bmarker:
    return SType.SAI
  else:
    return SType.SPython

def pipenames(a:LitreplArgs, st:SType)->FileNames:
  """ Return the interpreter state: input and output pipe names, pid, etc. If
  not explicitly specified in the config, the state is shared for all files in
  the current directory. """
  auxdir=join(a.auxdir if a.auxdir is not None else defauxdir(),st2name(st))
  return FileNames(auxdir, join(auxdir,"_in.pipe"), join(auxdir,"_out.pipe"),
                   join(auxdir,"_pid.txt"),join(auxdir,"_ecode.txt"))

PATTERN_PYTHON_1=('3256748426384\n',)*2
PATTERN_PYTHON_2=('325674801010\n',)*2
PATTERN_GPT4ALLCLI_1=('/echo 1121312\n', '1121312\n')
PATTERN_GPT4ALLCLI_2=('/echo 8893223\n', '8893223\n')

def attach(fns:FileNames)->Optional[Interpreter]:
  """ Attach to the interpreter associated with the given pipe filenames. """
  try:
    pid=readipid(fns)
    if pid is None:
      pdebug(f"could not determine pid of an interpreter")
      return None
    p=Process(pid)
    cmd=p.cmdline()
    cls=None
    if any('aicli' in w for w in cmd):
      cls=AicliInterpreter
    elif any('ipython' in w for w in cmd):
      cls=IPythonInterpreter
    elif any('python' in w for w in cmd):
      cls=PythonInterpreter
    else:
      assert False, f"Unknown interpreter {cmd}"
    pdebug(f"interpreter pid {pid} cmd '{cmd}' was resolved into '{cls}'")
    return cls(fns)
  except NoSuchProcess as p:
    pdebug(f"could not determine the interpreter classs for ({p})")
    return None

def open_child_pipes(inp,outp):
  return os.open(inp,os.O_RDWR|os.O_SYNC),os.open(outp,os.O_RDWR|os.O_SYNC);
def open_parent_pipes(inp,outp):
  return open(inp,'w'),open(outp,'r')

class PythonInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    wd,inp,outp,pid,ecode=astuple(fns)
    ret=system(
      f"exec {interpreter} -uic 'import sys; sys.ps1=\"\"; sys.ps2=\"\";' "
      f"<'{inp}' >'{outp}' 2>&1"
    )
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write(
      '\nimport signal\n'
      'def _handler(signum,frame):\n'
      '  raise KeyboardInterrupt()\n\n'
      '_=signal.signal(signal.SIGINT,_handler)\n'
    )
    if a.exception_exit is not None:
      finp.write(
        'import sys; import os\n'
        'def _exceptexithook(type,value,traceback):\n'
        f'  os._exit({a.exception_exit})\n\n'
        'sys.excepthook=_exceptexithook\n'
      )
  def patterns(self):
    return PATTERN_PYTHON_1,PATTERN_PYTHON_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    return text
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    return fillspaces(code, '# spaces')

class IPythonInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    assert 'ipython' in interpreter.lower()
    wd,inp,outp,pid,ecode=astuple(fns)
    cfg=join(wd,'litrepl_ipython_config.py')
    log=f"--logfile={join(wd,'_ipython.log')}" if DEBUG else ""
    with open(cfg,'w') as f:
      f.write(
        'import sys\n'
        # See https://github.com/ipython/ipython/issues/14246
        'sys.stdout.reconfigure(line_buffering=True)\n'
        'from IPython.terminal.prompts import Prompts, Token\n'
        'class EmptyPrompts(Prompts):\n'
        '  def in_prompt_tokens(self):\n'
        '    return [(Token.Prompt, "")]\n'
        '  def continuation_prompt_tokens(self, width=None):\n'
        '    return [(Token.Prompt, "") ]\n'
        '  def rewrite_prompt_tokens(self):\n'
        '    return []\n'
        '  def out_prompt_tokens(self):\n'
        '    return []\n'
        'c.TerminalInteractiveShell.prompts_class = EmptyPrompts\n'
        'c.TerminalInteractiveShell.separate_in = ""\n'
        'c.TerminalInteractiveShell.separate_out = ""\n'
      )
    ret=system(
      f"exec {interpreter} --config={cfg} --colors=NoColor {log} -i "
      f"<'{inp}' >'{outp}' 2>&1"
    )
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write(
      '\nimport signal\n'
      'def _handler(signum,frame):\n'
      '  raise KeyboardInterrupt()\n\n'
      '_=signal.signal(signal.SIGINT,_handler)\n'
    )
    if a.exception_exit is not None:
      finp.write(
        'import IPython; import os\n'
        'def _exithandler(*args, **kwargs):\n'
        f'  os._exit({int(a.exception_exit)})\n\n'
        'IPython.get_ipython().set_custom_exc((Exception,), _exithandler)\n'
      )
  def patterns(self):
    return PATTERN_PYTHON_1,PATTERN_PYTHON_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    # A workaround for https://github.com/ipython/ipython/issues/13622
    r=re.compile('ERROR! Session/line number was not unique in database. '
                 'History logging moved to new session [0-9]+\\n')
    return re.sub(r,'',text)
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    # IPython seems to not echo the terminating cpaste pattern into the output
    # which is good.
    paste_pattern='12341234213423'
    return (f'\n%cpaste -q -s {paste_pattern}\n{code}\n{paste_pattern}\n')

class AicliInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    ret=system(
      f"exec {interpreter} "
      f"--readline-prompt='' "
      f"<'{fns.inp}' >'{fns.outp}' 2>&1"
    )
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write("/echo ready\n")
  def patterns(self):
    return PATTERN_GPT4ALLCLI_1,PATTERN_GPT4ALLCLI_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    return text.strip()+"\n"
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    for secvar,ref in secvar_matches(copy(code)):
      if secvar[0]=='^':
        assert ref>=1, "Above reference must be greater or equal one"
        absref=es.nsec-ref
      elif secvar[0]=='v':
        assert ref>=1, "Below reference must be greater or equal one"
        absref=es.nsec+ref
      elif secvar[0]=='>':
        absref=ref
      else:
        raise ValueError("Invalid section variable {secvar}")
      code=code.replace(
        secvar,
        es.sres.get(
          absref,
          es.sr.preproc.results.get(absref,f'<invalid reference to section {absref}>').strip()
        )
      )
    return code + "/ask\n"

def write_child_pid(pidf,pid):
  with open(pidf,'w') as f:
    for attempt in range(20):
      try:
        f.write(str(Process(pid).children()[0].pid))
        return True
      except IndexError:
        sleep(0.1)
  return False

def start_(a:LitreplArgs,interpreter:str,i:Interpreter)->int:
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `_inp.pipe`, `_out.pipe`, `_pid.txt`."""
  fns=i.fns
  wd,inp,outp,pid,ecode=astuple(fns)
  makedirs(wd, exist_ok=True)
  if isfile(pid):
    system(f'kill -9 "$(cat {pid})" >/dev/null 2>&1')
  system(f"mkfifo '{inp}' '{outp}' 2>/dev/null")
  sys.stdout.flush(); sys.stderr.flush() # FIXME: to avoid duplicated stdout
  npid=os.fork()
  if npid==0:
    # sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    setpgid(getpid(),0)
    blind_unlink(ecode)
    open_child_pipes(inp,outp)
    ret=i.run_child(interpreter)
    ret=ret if ret<256 else WEXITSTATUS(ret)
    pdebug(f"fork records ecode: {ret}")
    with open(ecode,'w') as f:
      f.write(str(ret))
    exit(ret)
  else:
    finp,foutp=open_parent_pipes(inp,outp)
    i.setup_child(a,finp,foutp)
    if write_child_pid(pid,npid):
      return 0
    else:
      return 1

def start(a:LitreplArgs, st:SType)->int:
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
    assert not a.exception_exit, "Not supported"
    interpreter='aicli' if a.ai_interpreter=='auto' else a.ai_interpreter
    return start_(a,interpreter,AicliInterpreter(fns))
  else:
    raise ValueError(f"Unsupported section type: {st}")



def interp_code_preprocess(a:LitreplArgs, ss:Interpreter, es:EvalState, code:str) -> str:
  return ss.code_preprocess(a,es,code)

def interp_result_postprocess(a:LitreplArgs, ss:Interpreter, text:str) -> str:
  s=ss.result_postprocess(a,text)
  return wraplong(s,a.result_textwidth) if a.result_textwidth else s

def restart(a:LitreplArgs,st:SType):
  stop(a,st); start(a,st)

def running(a:LitreplArgs,st:SType)->bool:
  """ Checks if the background session was run or not. """
  fns=pipenames(a,st)
  return 0==system(f"test -f '{fns.pidf}' && test -p '{fns.inp}' && test -p '{fns.outp}'")

def stop(a:LitreplArgs,st:SType)->None:
  """ Stops the background Python session. """
  fns=pipenames(a,st)
  system(f'kill "$(cat {fns.pidf} 2>/dev/null)" >/dev/null 2>&1')
  system(f"rm '{fns.inp}' '{fns.outp}' '{fns.pidf}' >/dev/null 2>&1")


@dataclass
class SymbolsMarkdown:
  icodebeginmarker="```[ ]*ai|```[ ]*l?python|```[ ]*l?code|```[ ]*{[^}]*python[^}]*}"
  icodendmarker="```"
  ocodebeginmarker="```[ ]*l?result|```[ ]*{[^}]*result[^}]*}"
  ocodendmarker="```"
  verbeginmarker="<!--[ ]*l?result[ ]*-->"
  verendmarker="<!--[ ]*l?noresult[ ]*-->"
  aibeginmarker="<!--[ ]*ai[ ]*-->"
  aiendmarker="<!--[ ]*noai[ ]*-->"
  combeginmarker=r"<!--[ ]*l?ignore[ ]*-->"
  comendmarker=r"<!--[ ]*l?noignore[ ]*-->"

symbols_md=SymbolsMarkdown()

def toplevel_markers_markdown():
  sl=symbols_md
  return '|'.join([sl.icodebeginmarker,
                   sl.ocodebeginmarker,
                   sl.verbeginmarker,
                   sl.combeginmarker,
                   sl.aibeginmarker
                   ])

# For the `?!` syntax, see https://stackoverflow.com/questions/56098140/how-to-exclude-certain-possibilities-from-a-regular-expression
grammar_md = fr"""
start: (topleveltext)? (snippet (topleveltext)?)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | comsection -> e_comsection
comsection.2 : combeginmarker comtext comendmarker
icodesection.1 : icodebeginmarker ctext icodendmarker
               | aibeginmarker aitext aiendmarker
ocodesection.1 : ocodebeginmarker ctext ocodendmarker
               | verbeginmarker vertext verendmarker
icodebeginmarker : /{symbols_md.icodebeginmarker}/
icodendmarker : /{symbols_md.icodendmarker}/
aibeginmarker : /{symbols_md.aibeginmarker}/
aiendmarker : /{symbols_md.aiendmarker}/
ocodebeginmarker : /{symbols_md.ocodebeginmarker}/
ocodendmarker : /{symbols_md.ocodendmarker}/
verbeginmarker : /{symbols_md.verbeginmarker}/
verendmarker : /{symbols_md.verendmarker}/
inlinebeginmarker : "`"
inlinendmarker : "`"
combeginmarker : /{symbols_md.combeginmarker}/
comendmarker : /{symbols_md.comendmarker}/
topleveltext : /(.(?!{toplevel_markers_markdown()}))*./s
ctext : /(.(?!{symbols_md.ocodendmarker}|{symbols_md.icodendmarker}))*./s
comtext : /(.(?!{symbols_md.comendmarker}))*./s
vertext : /(.(?!{symbols_md.verendmarker}))*./s
aitext : /(.(?!{symbols_md.aiendmarker}))*./s
"""


@dataclass
class SymbolsLatex:
  icodebeginmarker=r"\\begin\{l[a-zA-Z0-9]*code\}|\\begin\{l?python\}|\\begin\{ai\}"
  icodendmarker=r"\\end\{l[a-zA-Z0-9]*code\}|\\end\{l?python\}|\\end\{ai\}"
  icodebeginmarker2=r"\%lcode"
  icodendmarker2=r"\%lnocode"
  ocodebeginmarker=r"\\begin\{l?[a-zA-Z0-9]*result\}"
  ocodendmarker=r"\\end\{l?[a-zA-Z0-9]*result\}"
  verbeginmarker=r"\%l?result"
  verendmarker=r"\%l?noresult"
  inlinemarker=r"\\l[a-zA-Z0-9]*inline"
  combeginmarker=r"\%lignore"
  comendmarker=r"\%lnoignore"

symbols_latex=SymbolsLatex()

OBR="{"
CBR="}"
BCBR="\\}"
BOBR="\\{"

def toplevel_markers_latex():
  sl=symbols_latex
  return '|'.join([sl.icodebeginmarker,sl.icodendmarker,
                   sl.icodebeginmarker2,sl.icodendmarker2,
                   sl.ocodebeginmarker,sl.ocodendmarker,
                   sl.verbeginmarker,sl.verendmarker,
                   sl.combeginmarker,sl.comendmarker,
                   sl.inlinemarker+BOBR])
grammar_latex = fr"""
start: (topleveltext)? (snippet (topleveltext)? )*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | inlinesection -> e_inline
        | comsection -> e_comment
comsection.2 : combeginmarker comtext comendmarker
icodesection.1 : icodebeginmarker innertext icodendmarker
               | icodebeginmarker2 innertext icodendmarker2
ocodesection.1 : ocodebeginmarker innertext ocodendmarker
               | verbeginmarker innertext verendmarker
inlinesection.1 : inlinemarker "{OBR}" inltext "{CBR}" spaces obr inltext cbr
inlinemarker : /{symbols_latex.inlinemarker}/
icodebeginmarker : /{symbols_latex.icodebeginmarker}/
icodendmarker : /{symbols_latex.icodendmarker}/
icodebeginmarker2 : /{symbols_latex.icodebeginmarker2}/
icodendmarker2 : /{symbols_latex.icodendmarker2}/
ocodebeginmarker : /{symbols_latex.ocodebeginmarker}/
ocodendmarker : /{symbols_latex.ocodendmarker}/
verbeginmarker : /{symbols_latex.verbeginmarker}/
verendmarker : /{symbols_latex.verendmarker}/
combeginmarker : /{symbols_latex.combeginmarker}/
comendmarker : /{symbols_latex.comendmarker}/
topleveltext : /(.(?!{toplevel_markers_latex()}))*./s
innertext : /(.(?!{symbols_latex.icodendmarker2}|{symbols_latex.icodendmarker}|{symbols_latex.ocodendmarker}|{symbols_latex.verendmarker}))*./s
inltext : ( /[^{OBR}{CBR}]+({OBR}[^{CBR}]*{CBR}[^{OBR}{CBR}]*)*/ )?
comtext : ( /(.(?!{symbols_latex.comendmarker}))*./s )?
spaces : ( /[ \t\r\n]+/s )?
obr : "{OBR}"
cbr : "{CBR}"
"""

def parse_(grammar, tty_ok=True):
  pdebug(f"parsing start")
  parser=Lark(grammar,propagate_positions=True)
  inp=sys.stdin.read() if (not isatty(sys.stdin.fileno()) or tty_ok) else ""
  tree=parser.parse(inp)
  pdebug(f"parsing finish")
  return tree

GRAMMARS={'markdown':grammar_md,'tex':grammar_latex,'latex':grammar_latex}
SYMBOLS={'markdown':symbols_md,'tex':symbols_latex,'latex':symbols_latex}

def eval_code(*args, **kwargs) -> str:
  res,_=eval_code_(*args, **kwargs)
  return res

def eval_code_(a:LitreplArgs,
               fns:FileNames,
               ss:Interpreter,
               es:EvalState,
               code:str,
               runr:Optional[RunResult]=None) -> Tuple[str,ReadResult]:
  """ Start or complete the snippet evaluation process. `runr`
  contains the already existing runner's context, if any.

  The function returns either the evaluation result or the running context
  encoded in the result for later reference.
  """
  rr:ReadResult
  if runr is None:
    rr,runr=processAdapt(a,fns,ss,
                         interp_code_preprocess(a,ss,es,code),
                         a.timeout_initial)
  else:
    rr=processCont(a,fns,ss,runr,a.timeout_continue)
  pptext=interp_result_postprocess(a,ss,rr.text)
  res=rresultSave(pptext,runr) if rr.timeout else pptext
  return res,rr

def secvar_matches(code:str)->Iterable[Tuple[str,int]]:
  for secvar in re.findall(SECVAR_RE,code):
    secvar=[m for m in secvar if len(m)>0][0]
    idx=int(''.join([c for c in secvar if c.isdigit()]))
    yield str(secvar),idx


def eval_section_(a:LitreplArgs, tree, sr:SecRec, interrupt:bool=False)->ECode:
  """ Evaluate code sections of the parsed `tree`, as specified in the `sr`
  request.  """
  nsecs=sr.nsecs
  es=EvalState(sr)

  def _getinterp(bmarker:str)->Tuple[FileNames,Optional[Interpreter]]:
    st=bmarker2st(bmarker)
    es.stypes.add(st)
    fns=pipenames(a,st)
    if not running(a,st):
      start(a,st)
    ss=attach(fns)
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

  def _checkecode(fns,nsec,pending:bool)->ECode:
    ec=interpExitCode(fns)
    pdebug(f"interpreter exit code: {ec}")
    if ec is ECODE_RUNNING:
      if pending and a.pending_exit:
        es.ecodes[nsec]=a.pending_exit
      else:
        es.ecodes[nsec]=ECODE_RUNNING
    else:
      es.ecodes[nsec]=ec
    return ec

  def _failmsg(fns,ec):
    return f"<Interpreter exited with code: {ec}>\n"

  class C(LarkInterpreter):
    def _print(self, s:str):
      print(s, end='')
    def text(self,tree):
      self._print(tree.children[0].value)
    def topleveltext(self,tree):
      return self.text(tree)
    def innertext(self,tree):
      return self.text(tree)
    def icodesection(self,tree):
      es.nsec+=1
      bmarker=tree.children[0].children[0].value
      t=tree.children[1].children[0].value
      emarker=tree.children[2].children[0].value
      self._print(f"{bmarker}{t}{emarker}")
      bm,em=tree.children[0].meta,tree.children[2].meta
      code=unindent(bm.column-1,t)
      if es.nsec in nsecs:
        fns,ss=_getinterp(bmarker)
        rr=None
        if ss:
          es.sres[es.nsec],rr=eval_code_(a,fns,ss,es,code,sr.preproc.pending.get(es.nsec))
        ec=_checkecode(fns,es.nsec,rr.timeout if rr else False)
        if ec is not None:
          msg=_failmsg(fns,ec)
          pstderr(msg)
          es.sres[es.nsec]=es.sres.get(es.nsec,'')+msg
    def ocodesection(self,tree):
      bmarker=tree.children[0].children[0].value
      t=tree.children[1].children[0].value
      emarker=tree.children[2].children[0].value
      bm,em=tree.children[0].meta,tree.children[2].meta
      if es.nsec in nsecs:
        assert es.nsec in es.sres
        t2=bmarker+"\n"+indent(bm.column-1,
                               escape(es.sres[es.nsec],emarker)+emarker)
        es.ledder[bm.line]=nlines(t2)-nlines(t)
        self._print(t2)
      else:
        self._print(f"{bmarker}{tree.children[1].children[0].value}{emarker}")
    def inlinesection(self,tree):
      # FIXME: Latex-only
      bm,em=tree.children[0].meta,tree.children[4].meta
      code=tree.children[1].children[0].value
      spaces=tree.children[2].children[0].value if tree.children[2].children else ''
      im=tree.children[0].children[0].value
      if es.nsec in nsecs:
        fns,ss=_getinterp("python")
        if ss:
          result=process(a,fns,ss,'print('+code+');\n')[0].rstrip('\n')
        ec=_checkecode(fns,es.nsec,False)
        if ec is not None:
          pusererror(_failmsg(fns,ec))
      else:
        result=tree.children[4].children[0].value if tree.children[4].children else ''
      self._print(f"{im}{OBR}{code}{CBR}{spaces}{OBR}{result}{CBR}")
    def comsection(self,tree):
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      self._print(f"{bmarker}{tree.children[1].children[0].value}{emarker}")

  def _finally():
    if a.map_cursor:
      cl=a.map_cursor[0] # cursor line
      for threshold,diff in sorted(es.ledder.items()):
        if cl>threshold:
          cl=max(threshold,cl+diff)
      with open(a.map_cursor_output,"w") as f:
        f.write(str(cl))
    if a.foreground:
      for st in es.stypes:
        stop(a,st)

  with with_parent_finally(_finally):
    C().visit(tree)

  pdebug(f"eval_code_ ecodes {es.ecodes}")
  return max(map(lambda x:ECODE_OK if x is None else x,
                 es.ecodes.values()),default=ECODE_OK)

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
    def icodesection(self,tree):
      self.nsec+=1
      self._count(tree.children[0].meta,tree.children[2].meta)
    def ocodesection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
      contents=tree.children[1].children[0].value
      bm,em=tree.children[0].meta,tree.children[2].meta
      self._getrr(contents,bm.column-1)
    def oversection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
      self._getrr(tree.children[1].children[0].value)
    def inlinesection(self,tree):
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

def solve_sloc(s:str, tree)->SecRec:
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


def status(a:LitreplArgs,sts:List[SType],version):
  if a.verbose:
    return status_verbose(a,sts,version)
  else:
    return status_oneline(a,sts)

def status_oneline(a:LitreplArgs,sts:List[SType])->int:
  for st in sts:
    fns=pipenames(a,st)
    auxd,inp,outp,pidf,ecodef=astuple(fns)
    pdebug(f"status auxdir: {auxd}")
    try:
      pid=open(pidf).read().strip()
      cmd=' '.join(Process(int(pid)).cmdline())
    except Exception as ex:
      pdebug(f"exception: {ex}")
      pid='-'
      cmd='-'
    try:
      ecode=open(ecodef).read().strip()
    except Exception:
      ecode='-'
    print(f"{st2name(st):6s} {pid:10s} {ecode:3s} {cmd}")


def status_verbose(a:LitreplArgs,sts:List[SType],version:str)->int:
  print(f"version: {version}")
  print(f"workdir: {getcwd()}")
  print(f"litrepl PATH: {environ.get('PATH','')}")
  ecodes=set()
  for st in sts:
    fns=pipenames(a,st)
    auxd,inp,outp,pidf,_=astuple(fns)
    print(f"{st2name(st)} interpreter auxdir: {auxd}")
    try:
      pid=open(pidf).read().strip()
      print(f"{st2name(st)} interpreter pid: {pid}")
    except Exception:
      print(f"{st2name(st)} interpreter pid: ?")

    t=parse_(GRAMMARS[a.filetype], a.tty)
    sr=solve_sloc('0..$',t)
    for nsec,pend in sr.preproc.pending.items():
      fname=pend.fname
      print(f"{st2name(st)} pending section {nsec} buffer: {fname}")
      try:
        for bline in check_output(['lsof','-t',fname], stderr=DEVNULL).split(b'\n'):
          line=bline.decode('utf-8')
          if len(line)==0:
            continue
          print(f"{st2name(st)} pending section {nsec} reader: {line}")
      except CalledProcessError:
        print(f"{st2name(st)} pending section {nsec} reader: ?")
    if st==SType.SPython:
      ss=attach(fns)
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
    else:
      raise NotImplementedError(f'Unsupported type {st}')
    ecode=interpExitCode(fns)
    ecodes.add(0 if ecode is None else ecode)
  return max(ecodes)
