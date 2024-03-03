import os
import sys
import fcntl
import re

from copy import deepcopy
from typing import List, Optional, Tuple, Set, Dict, Callable, Any
from select import select
from os import environ, system, isatty
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter
from os.path import isfile, join
from signal import signal, SIGINT
from time import sleep, time
from dataclasses import dataclass, astuple
from functools import partial
from argparse import ArgumentParser
from collections import defaultdict
from os import makedirs, getuid, getcwd
from tempfile import gettempdir
from hashlib import sha256
from psutil import Process

from .types import (PrepInfo, RunResult, NSec, FileName, SecRec,
                    FileNames, IType, Settings, CursorPos)
from .eval import (process, pstderr, rresultLoad, rresultSave, processAdapt,
                   processCont, interpExitCodeNB)
from .utils import(unindent, indent, escape, fillspaces, fmterror, cursor_within)

DEBUG:bool=False
LitreplArgs=Any

def pdebug(*args,**kwargs):
  if DEBUG:
    print(f"[{time():14.3f}]", *args, file=sys.stderr, **kwargs, flush=True)

def defauxdir(suffix:Optional[str]=None)->str:
  """ Generate the default name of working directory. """
  suffix_=f"{suffix}_" if suffix is not None else ""
  return join(gettempdir(),f"litrepl_{getuid()}_"+suffix_+
              sha256(getcwd().encode('utf-8')).hexdigest()[:6])

def pipenames(a:LitreplArgs)->FileNames:
  """ Return the interpreter state: input and output pipe names, pid, etc. If
  not explicitly specified in the config, the state is shared for all files in
  the current directory. """
  auxdir=a.auxdir if a.auxdir is not None else defauxdir()
  return FileNames(auxdir, join(auxdir,"_in.pipe"), join(auxdir,"_out.pipe"),
                   join(auxdir,"_pid.txt"),join(auxdir,"_ecode.txt"))

def settings(fns:FileNames)->Optional[Settings]:
  """ Determines the session settings. Currently just finds out the type of the
  interpreter. """
  try:
    pid=int(open(fns.pidf).read())
    p=Process(pid)
    cmd=p.cmdline()
    itype = None
    if any('ipython' in w for w in cmd):
      itype = IType.IPython
    elif any('python' in w for w in cmd):
      itype = IType.Python
    pdebug(f"interpreter pid {pid} cmd '{cmd}' leads to type '{itype}'")
    return Settings(itype)
  except FileNotFoundError:
    return None

def fork_python(a:LitreplArgs, name:str):
  """ Forks an instance of Python interpreter `name` """
  assert 'python' in name
  wd,inp,outp,pid,ecode=astuple(pipenames(a))
  system(('{ '
          f'rm "{ecode}" 2>/dev/null;'
          f'{name} -uic "import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          f'os.open(\'{inp}\',os.O_RDWR|os.O_SYNC);'
          f'os.open(\'{outp}\',os.O_RDWR|os.O_SYNC);"'
          f'<"{inp}" >"{outp}" 2>&1 ;'
          f'echo "$?">"{ecode}";'
          '} & '
          f'echo $! >"{pid}"'))
  inp=open(inp,'w')
  inp.write(
    '\nimport signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n'
  )
  if a.exception_exit is not None:
    inp.write(
      'import sys\n'
      'import os\n'
      'def _exceptexithook(type,value,traceback):\n'
      f'  os._exit({int(a.exception_exit)})\n\n'
      'sys.excepthook=_exceptexithook\n'
    )
  exit(0)

def fork_ipython(a:LitreplArgs, name:str):
  """ Forks an instance of IPython interpreter `name` """
  assert 'ipython' in name
  wd,inp,outp,pid,ecode=astuple(pipenames(a))
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
  system(('{ '
          f'rm "{ecode}" 2>/dev/null;'
          f'{name} -um IPython --config={cfg} --colors=NoColor {log} -c '
          f'"import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          f'os.open(\'{inp}\',os.O_RDWR|os.O_SYNC);'
          f'os.open(\'{outp}\',os.O_RDWR|os.O_SYNC);"'
          f' -i <"{inp}" >"{outp}" 2>&1 ;'
          f'echo "$?">"{ecode}";'
          '} & '
          f'echo $! >"{pid}"'))
  f=open(inp,'w')
  f.write(
    '\nimport signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n'
  )
  if a.exception_exit is not None:
    f.write(
      'import IPython\n'
      'def _exithandler(*args, **kwargs):\n'
      f'  os._exit({int(a.exception_exit)})\n\n'
      'IPython.get_ipython().set_custom_exc((Exception,), _exithandler)\n'
    )
  exit(0)


def code_preprocess_ipython(code:str) -> str:
  # IPython seems to not echo the terminating cpaste pattern into the output
  # which is good.
  paste_pattern='12341234213423'
  return (f'\n%cpaste -q -s {paste_pattern}\n{code}\n{paste_pattern}\n')
def text_postprocess_ipython(text:str) -> str:
  # A workaround for https://github.com/ipython/ipython/issues/13622
  r=re.compile('ERROR! Session/line number was not unique in database. '
               'History logging moved to new session [0-9]+\\n')
  return re.sub(r,'',text)

# def code_preprocess_ipython(code:str) -> str:
#   return fillspaces(code, '# spaces')
# def text_postprocess_ipython(text:str) -> str:
#   return text

def code_preprocess_python(code:str) -> str:
  return fillspaces(code, '# spaces')
def text_postprocess_python(text:str) -> str:
  return text


def code_preprocess(ss:Settings, code:str) -> str:
  if (ss.itype is None) or ss.itype == IType.IPython:
    return code_preprocess_ipython(code)
  elif ss.itype == IType.Python:
    return code_preprocess_python(code)
  else:
    raise ValueError(fmterr(f'''
      Interpreter type {ss.itype} is not supported for pre-processing. Did you
      restart LitRepl after an update?
    '''))

def text_postprocess(ss:Settings, text:str) -> str:
  if (ss.itype is None) or ss.itype == IType.IPython:
    return text_postprocess_ipython(text)
  elif ss.itype == IType.Python:
    return text_postprocess_python(text)
  else:
    raise ValueError(fmterr(f'''
      Interpreter type {ss.itype} is not supported for post-processing. Did you
      restart LitRepl after an update?
    '''))

def start_(a:LitreplArgs, fork_handler:Callable[...,None])->None:
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `_inp.pipe`, `_out.pipe`, `_pid.txt`."""
  wd,inp,outp,pid,_=astuple(pipenames(a))
  makedirs(wd, exist_ok=True)
  if isfile(pid):
    system(f'kill -9 "$(cat {pid})" >/dev/null 2>&1')
  system(f"mkfifo '{inp}' '{outp}' 2>/dev/null")
  if os.fork()==0:
    sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    fork_handler()
  else:
    for i in range(20):
      if isfile(pid):
        break
      sleep(0.5)
    if not isfile(pid):
      raise ValueError(f"Couldn't see '{pid}'. Did the fork fail?")

def start(a:LitreplArgs):
  if 'ipython' in a.interpreter:
    start_(a, partial(fork_ipython,a=a,name=a.interpreter))
  elif 'python' in a.interpreter:
    start_(a, partial(fork_python,a=a,name=a.interpreter))
  elif a.interpreter=='auto':
    if system('python -m IPython -c \'print("OK")\' >/dev/null 2>&1')==0:
      start_(a, partial(fork_ipython,a=a,name='ipython'))
    else:
      start_(a, partial(fork_python,a=a,name='python'))
  else:
    raise ValueError(f"Unsupported interpreter '{a.interpreter}'")

def running(a:LitreplArgs)->bool:
  """ Checks if the background session was run or not. """
  fns=pipenames(a)
  return 0==system(f"test -f '{fns.pidf}' && test -p '{fns.inp}' && test -p '{fns.outp}'")

def stop(a:LitreplArgs)->None:
  """ Stops the background Python session. """
  fns=pipenames(a)
  system(f'kill "$(cat {fns.pidf} 2>/dev/null)" >/dev/null 2>&1')
  system(f"rm '{fns.inp}' '{fns.outp}' '{fns.pidf}' >/dev/null 2>&1")


@dataclass
class SymbolsMarkdown:
  icodebeginmarker="```[ ]*l?python|```[ ]*l?code|```[ ]*{[^}]*python[^}]*}"
  icodendmarker="```"
  ocodebeginmarker="```[ ]*l?result|```[ ]*{[^}]*result[^}]*}"
  ocodendmarker="```"
  verbeginmarker="<!--[ ]*l?result[ ]*-->"
  verendmarker="<!--[ ]*l?noresult[ ]*-->"
  icodebeginmarker2="<!--[ ]*l?code"
  icodendmarker2="(l?(no)?code)?-->"
  verbeginmarker2="<!--[ ]*l?result"
  verendmarker2="(l?(no)?result)?-->"
  combeginmarker=r"<!--[ ]*l?ignore[ ]*-->"
  comendmarker=r"<!--[ ]*l?noignore[ ]*-->"

symbols_md=SymbolsMarkdown()

grammar_md = fr"""
start: (text)? (snippet (text)?)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | comsection -> e_comsection
comsection.2 : combeginmarker comtext comendmarker
icodesection.1 : icodebeginmarker ctext icodendmarker
               | icodebeginmarker2 ctext2 icodendmarker2
ocodesection.1 : ocodebeginmarker ctext ocodendmarker
               | verbeginmarker ctext verendmarker
               | verbeginmarker2 ctext2 verendmarker2
icodebeginmarker : /{symbols_md.icodebeginmarker}/
icodendmarker : /{symbols_md.icodendmarker}/
icodebeginmarker2 : /{symbols_md.icodebeginmarker2}/
icodendmarker2 : /{symbols_md.icodendmarker2}/
ocodebeginmarker : /{symbols_md.ocodebeginmarker}/
ocodendmarker : /{symbols_md.ocodendmarker}/
verbeginmarker : /{symbols_md.verbeginmarker}/
verendmarker : /{symbols_md.verendmarker}/
verbeginmarker2 : /{symbols_md.verbeginmarker2}/
verendmarker2 : /{symbols_md.verendmarker2}/
inlinebeginmarker : "`"
inlinendmarker : "`"
combeginmarker : /{symbols_md.combeginmarker}/
comendmarker : /{symbols_md.comendmarker}/
text : /(.(?!{symbols_md.ocodebeginmarker}|{symbols_md.icodebeginmarker}|{symbols_md.icodebeginmarker2}|{symbols_md.verbeginmarker}|{symbols_md.verbeginmarker2}|{symbols_md.combeginmarker}))*./s
ctext : /(.(?!{symbols_md.ocodendmarker}|{symbols_md.icodendmarker}|{symbols_md.verendmarker}))*./s
ctext2 : /(.(?!{symbols_md.icodendmarker2}|{symbols_md.verendmarker2}))*./s
comtext : /(.(?!{symbols_md.comendmarker}))*./s
"""


@dataclass
class SymbolsLatex:
  icodebeginmarker=r"\\begin\{l[a-zA-Z0-9]*code\}"
  icodendmarker=r"\\end\{l[a-zA-Z0-9]*code\}"
  icodebeginmarker2=r"\%lcode"
  icodendmarker2=r"\%lnocode"
  ocodebeginmarker=r"\\begin\{l[a-zA-Z0-9]*result\}"
  ocodendmarker=r"\\end\{l[a-zA-Z0-9]*result\}"
  verbeginmarker=r"\%lresult"
  verendmarker=r"\%lnoresult"
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

def eval_code(a:LitreplArgs,
              fns:FileNames,
              ss:Settings,
              code:str,
              runr:Optional[RunResult]=None) -> str:
  """ Start or complete the code snippet evaluation process.  `RunResult` may
  contain the existing runner's context.

  The function returns either the evaluation result or the running context
  encoded in the result for later reference.
  """
  if runr is None:
    rr,runr=processAdapt(fns,code_preprocess(ss,code),a.timeout_initial)
  else:
    rr=processCont(fns,runr,a.timeout_continue)
  return rresultSave(rr.text,runr) if rr.timeout else text_postprocess(ss,rr.text)

def eval_section_(a:LitreplArgs, tree, secrec:SecRec)->int:
  """ Evaluate code sections of the parsed `tree`, as specified in the `secrec`
  request.  """
  if not running(a) or a.standalone_session:
    start(a)
  fns=pipenames(a)
  ss=settings(fns)
  assert ss is not None
  nsecs=secrec.nsecs
  ssrc:Dict[int,str]={} # Section sources
  sres:Dict[int,str]={} # Section results
  class C(Interpreter):
    def __init__(self):
      self.nsec=-1
    def text(self,tree):
      print(tree.children[0].value, end='')
    def topleveltext(self,tree):
      return self.text(tree)
    def innertext(self,tree):
      return self.text(tree)
    def icodesection(self,tree):
      self.nsec+=1
      t=tree.children[1].children[0].value
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      print(f"{bmarker}{t}{emarker}", end='')
      bm,em=tree.children[0].meta,tree.children[2].meta
      code=unindent(bm.column-1,t)
      ssrc[self.nsec]=code
      if self.nsec in nsecs:
        sres[self.nsec]=eval_code(a,fns,ss,code,secrec.pending.get(self.nsec))
    def ocodesection(self,tree):
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      bm,em=tree.children[0].meta,tree.children[2].meta
      if self.nsec in nsecs:
        assert self.nsec in sres
        print(bmarker+"\n"+indent(bm.column-1,
                                  escape(sres[self.nsec],emarker)+
                                  emarker), end='')
      else:
        print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
    def inlinesection(self,tree):
      # FIXME: Latex-only
      bm,em=tree.children[0].meta,tree.children[4].meta
      code=tree.children[1].children[0].value
      spaces=tree.children[2].children[0].value if tree.children[2].children else ''
      im=tree.children[0].children[0].value
      if self.nsec in nsecs:
        result=process(fns,'print('+code+');\n')[0].rstrip('\n')
      else:
        result=tree.children[4].children[0].value if tree.children[4].children else ''
      print(f"{im}{OBR}{code}{CBR}{spaces}{OBR}{result}{CBR}", end='')
    def comsection(self,tree):
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
  C().visit(tree)
  ecode=interpExitCodeNB(fns,notfound=200)
  if a.standalone_session:
    stop(a)
  return ecode

def solve_cpos(tree, cs:List[CursorPos])->PrepInfo:
  """ Preprocess the document tree. Resolve the list of cursor locations `cs`
  into code section numbers. """
  acc:dict={}
  rres:Dict[NSec,Set[RunResult]]=defaultdict(set)
  class C(Interpreter):
    def __init__(self):
      self.nsec=-1
    def _count(self,bm,em):
      for (line,col) in cs:
        if cursor_within((line,col),(bm.line,bm.column),
                                    (em.end_line,em.end_column)):
          acc[(line,col)]=self.nsec
    def _getrr(self,text):
      text1,pend=rresultLoad(text)
      if pend is not None:
        rres[self.nsec].add(pend)
    def icodesection(self,tree):
      self.nsec+=1
      self._count(tree.children[0].meta,tree.children[2].meta)
    def ocodesection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
      self._getrr(tree.children[1].children[0].value)
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
  return PrepInfo(c.nsec,acc,rres2)

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
    ppi.pending)

def status(a:LitreplArgs,version:str)->int:
  if a.standalone_session:
    start(a)
  fns=pipenames(a)
  auxd,inp,outp,pidf,_=astuple(fns)
  print(f"version: {version}")
  print(f"workdir: {getcwd()}")
  print(f"auxdir: {auxd}")
  try:
    pid=open(pidf).read().strip()
    print(f"interpreter pid: {pid}")
  except Exception:
    print(f"interpreter pid: -")
  t=parse_(GRAMMARS[a.filetype], a.tty)
  sr=solve_sloc('0..$',t)
  for nsec,pend in sr.pending.items():
    fname=pend.fname
    print(f"pending section {nsec} buffer: {fname}")
    try:
      for bline in check_output(['lsof','-t',fname], stderr=DEVNULL).split(b'\n'):
        line=bline.decode('utf-8')
        if len(line)==0:
          continue
        print(f"pending section {nsec} reader: {line}")
    except CalledProcessError:
      print(f"pending section {nsec} reader: -")
  ss=settings(fns)
  try:
    assert ss is not None
    interpreter_path=eval_code(a,fns,ss,'\n'.join(["import os","print(os.environ.get('PATH',''))"]))
    print(f"interpreter PATH: {interpreter_path.strip()}")
  except Exception:
    print(f"interpreter PATH: ?")
  try:
    assert ss is not None
    interpreter_pythonpath=eval_code(a,fns,ss,'\n'.join(["import sys","print(':'.join(sys.path))"]))
    print(f"interpreter PYTHONPATH: {interpreter_pythonpath.strip()}")
  except Exception:
    print(f"interpreter PYTHONPATH: ?")
  ecode=interpExitCodeNB(fns,notfound=200)
  if a.standalone_session:
    stop(a)
  return ecode
