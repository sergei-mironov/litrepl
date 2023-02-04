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
from collections import defaultdict

from .types import PrepInfo, RunResult, NSec, FileName, SecRec
from .eval import (process, pstderr, rresultLoad, rresultSave, processAdapt,
                   processCont)

def fork_python(name):
  assert 'python' in name
  system((f'{name} -uic "import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          'os.open(\'_inp.pipe\',os.O_RDWR|os.O_SYNC);'
          'os.open(\'_out.pipe\',os.O_RDWR|os.O_SYNC);"'
          '<_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
  open('_inp.pipe','w').write(
    'import signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n')
  exit(0)

def fork_ipython(name):
  assert 'ipython' in name
  open('/tmp/litrepl_ipython_config.py','w').write(
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
  system((f'{name} -um IPython --config=/tmp/litrepl_ipython_config.py --colors=NoColor --logfile=_ipython.log -c '
          '"import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          'os.open(\'_inp.pipe\',os.O_RDWR|os.O_SYNC);'
          'os.open(\'_out.pipe\',os.O_RDWR|os.O_SYNC);"'
          ' -i <_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
  open('_inp.pipe','w').write(
    'import signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n'
  )
  exit(0)

def start_(fork_handler:Callable[...,None])->None:
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `_inp.pipe`, `_out.pipt`, `_pid.txt`."""
  if isfile('_pid.txt'):
    system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('chmod -R +w _pylightnix 2>/dev/null && rm -rf _pylightnix')
  system('mkfifo _inp.pipe _out.pipe 2>/dev/null')
  if os.fork()==0:
    sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    fork_handler()
  else:
    for i in range(10):
      if isfile("_pid.txt"):
        break
      sleep(0.5)
    if not isfile("_pid.txt"):
      raise ValueError("Couldn't see '_pid.txt'. Did the fork fail?")

def start(a):
  if 'ipython' in a.interpreter:
    start_(partial(fork_ipython,name=a.interpreter))
  elif 'python' in a.interpreter:
    start_(partial(fork_python,name=a.interpreter))
  elif a.interpreter=='auto':
    if system('python -m IPython -c \'print("OK")\' >/dev/null 2>&1')==0:
      start_(partial(fork_ipython,name='ipython'))
    else:
      start_(partial(fork_python,name='python'))
  else:
    raise ValueError(f"Unsupported interpreter '{a.interpreter}'")

def running()->bool:
  """ Checks if the background session was run or not. """
  return 0==system("test -f _pid.txt && test -p _inp.pipe && test -p _out.pipe")

def stop():
  """ Stops the background Python session. """
  system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('rm _inp.pipe _out.pipe _pid.txt')


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

def toplevel_markers_latex():
  sl=symbols_latex
  return '|'.join([sl.icodebeginmarker,sl.icodendmarker,
                   sl.icodebeginmarker2,sl.icodendmarker2,
                   sl.ocodebeginmarker,sl.ocodendmarker,
                   sl.verbeginmarker,sl.verendmarker,
                   sl.combeginmarker,sl.comendmarker,
                   sl.inlinemarker])
OBR="{"
CBR="}"
BCBR="\\}"
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

def parse_(grammar):
  parser = Lark(grammar,propagate_positions=True)
  # print(parser)
  tree=parser.parse(sys.stdin.read())
  # print(tree.pretty())
  return tree

GRAMMARS={'markdown':grammar_md,'tex':grammar_latex,'latex':grammar_latex}
SYMBOLS={'markdown':symbols_md,'tex':symbols_latex,'latex':symbols_latex}

def cursor_within(pos, posA, posB)->bool:
  if pos[0]>posA[0] and pos[0]<posB[0]:
    return True
  else:
    if pos[0]==posA[0]:
      return pos[1]>=posA[1]
    elif pos[0]==posB[0]:
      return pos[1]<posB[1]
    else:
      return False

def unindent(col:int,lines:str)->str:
  def _rmspaces(l):
    return l[col:] if l.startswith(' '*col) else l
  return '\n'.join(map(_rmspaces,lines.split('\n')))

def indent(col,lines:str)->str:
  return '\n'.join([' '*col+l for l in lines.split('\n')])

def escape(text,pat):
  epat=''.join(['\\'+c for c in pat])
  return text.replace(pat,epat)

def eval_section_(a, tree, secrec:SecRec, force_code:Optional[str]=None)->None:
  nsecs=secrec.nsecs
  if not running():
    start(a)
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
        runr:Optional[RunResult]=secrec.pending.get(self.nsec)
        if runr is None:
          rr,runr=processAdapt(code if force_code is None else force_code,
                               a.timeout_initial)
        else:
          rr=processCont(runr,a.timeout_continue)
        sres[self.nsec]=rresultSave(rr.text,runr) if rr.timeout else rr.text
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
        result=process('print('+code+');\n').rstrip('\n')
      else:
        result=tree.children[4].children[0].value if tree.children[4].children else ''
      print(f"{im}{OBR}{code}{CBR}{spaces}{OBR}{result}{CBR}", end='')
    def comsection(self,tree):
      bmarker=tree.children[0].children[0].value
      emarker=tree.children[2].children[0].value
      print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
  C().visit(tree)

def solve_cpos(tree,cs:List[Tuple[int,int]])->PrepInfo:
  """ Solve the list of cursor positions into a set of section numbers. Also
  return the number of the last section. """
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

def solve_sloc(s:str,tree)->SecRec:
  p=Lark(grammar_sloc)
  t=p.parse(s)
  nknown:Dict[int,int]={}
  nqueries:Dict[int,Tuple[int,int]]={}
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

