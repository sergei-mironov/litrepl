#!/usr/bin/env python3

# from pylightnix import *

from typing import List, Optional, Tuple, Set, Dict
from re import search, match as re_match
import re
import os
import sys
import fcntl
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

def readout(fdr, prompt=mkre('>>>'),timeout:Optional[int]=10)->str:
  acc:bytes=b''
  while select([fdr],[],[],timeout)[0] != []:
    r=os.read(fdr, 1024)
    if r==b'':
      return acc.decode('utf-8')
    acc+=r
    m=re_match(prompt,acc)
    if m:
      ans=m.group(1)
      return ans.decode('utf-8')
  return acc.decode('utf-8').replace("\n","|")

def interact(fdr, fdw, text:str)->str:
  os.write(fdw,'3256748426384\n'.encode())
  x=readout(fdr,prompt=mkre('3256748426384\n'))
  os.write(fdw,text.encode())
  os.write(fdw,'\n'.encode())
  os.write(fdw,'3256748426384\n'.encode())
  res=readout(fdr,prompt=mkre('3256748426384\n'))
  return res

def process(lines:str)->str:
  pid=int(open('_pid.txt').read())
  fdr=0; fdw=0; prev=None
  try:
    fdw=os.open('_inp.pipe', os.O_WRONLY | os.O_SYNC)
    fdr=os.open('_out.pipe', os.O_RDONLY | os.O_SYNC)
    if fdw<0 or fdr<0:
      return f"ERROR: litrepl.py couldn't open session pipes\n"
    def _handler(signum,frame):
      os.kill(pid,SIGINT)
    prev=signal(SIGINT,_handler)
    fcntl.flock(fdw,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fcntl.flock(fdr,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return interact(fdr,fdw,lines)
  except BlockingIOError:
    return "ERROR: litrepl.py couldn't lock the sessions pipes\n"
  finally:
    if prev is not None:
      signal(SIGINT,prev)
    if fdr!=0:
      os.close(fdr)
    if fdw!=0:
      os.close(fdw)

def fork_python(name):
  assert name.startswith('python')
  system((f'{name} -uic "import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          'os.open(\'_inp.pipe\',os.O_RDWR);'
          'os.open(\'_out.pipe\',os.O_RDWR);"'
          '<_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
  open('_inp.pipe','w').write(
    'import signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n')
  exit(0)

def fork_ipython(name):
  assert name.startswith('ipython')
  open('_config.py','w').write(
    'from IPython.terminal.prompts import Prompts, Token\n'
    'class EmptyPrompts(Prompts):\n'
    '    def in_prompt_tokens(self):\n'
    '        return [(Token.Prompt, "")]\n'
    '    def continuation_prompt_tokens(self, width=None):\n'
    '        return [(Token.Prompt, "") ]\n'
    '    def rewrite_prompt_tokens(self):\n'
    '        return []\n'
    '    def out_prompt_tokens(self):\n'
    '        return []\n'
    'c.TerminalInteractiveShell.prompts_class = EmptyPrompts\n'
    'c.TerminalInteractiveShell.separate_in = ""\n'
    'c.TerminalInteractiveShell.separate_out = ""\n'
    )
  system((f'{name} --config=_config.py --debug --logfile=_ipython.log -c '
          '"import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
          'os.open(\'_inp.pipe\',os.O_RDWR);'
          'os.open(\'_out.pipe\',os.O_RDWR);"'
          ' -i <_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
  open('_inp.pipe','w').write(
    'import signal\n'
    'def _handler(signum,frame):\n'
    '  raise KeyboardInterrupt()\n\n'
    '_=signal.signal(signal.SIGINT,_handler)\n'
  )
  exit(0)

def start_(fork_handler:callable):
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
    if system('which ipython >/dev/null')==0:
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
  icodebeginmarker="```python"
  icodendmarker="```"
  ocodebeginmarker="```"
  ocodendmarker="```"
  verbeginmarker="<!--litrepl-->"
  verendmarker="<!--litrepl-->"
  combeginmarker=r"<!--lignore-->"
  comendmarker=r"<!--lnoignore-->"

symbols_md=SymbolsMarkdown()

grammar_md = fr"""
start: (text)? (snippet (text)?)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | oversection -> e_versection
        | comsection -> e_comsection
        // | text -> e_text
        // | inlinesection -> e_inline
comsection.2 : combeginmarker comtext comendmarker
icodesection.1 : icodebeginmarker text icodendmarker
ocodesection.1 : ocodebeginmarker text ocodendmarker
oversection.1 : verbeginmarker text verendmarker
// inlinesection : inlinebeginmarker text inlinendmarker
icodebeginmarker : "{symbols_md.icodebeginmarker}"
icodendmarker : "{symbols_md.icodendmarker}"
ocodebeginmarker : "{symbols_md.ocodebeginmarker}"
ocodendmarker : "{symbols_md.ocodendmarker}"
verbeginmarker : "<!--litrepl-->"
verendmarker : "<!--litrepl-->"
inlinebeginmarker : "`"
inlinendmarker : "`"
combeginmarker : "{symbols_md.combeginmarker}"
comendmarker : "{symbols_md.comendmarker}"
text : /(.(?!```|<\!--litrepl-->|{symbols_md.combeginmarker}|{symbols_md.comendmarker}))*./s
comtext : /(.(?!{symbols_md.comendmarker}))*./s
"""


@dataclass
class SymbolsLatex:
  icodebeginmarker=r"\begin{lcode}"
  icodendmarker=r"\end{lcode}"
  ocodebeginmarker=r"\begin{lresult}"
  ocodendmarker=r"\end{lresult}"
  verbeginmarker=r"%\begin{lresult}"
  verendmarker=r"%\end{lresult}"
  inlinemarker=r"\linline"
  combeginmarker=r"%lignore"
  comendmarker=r"%lnoignore"

symbols_latex=SymbolsLatex()
icodebeginmarkerE=r"\\begin\{lcode\}"
icodendmarkerE=r"\\end\{lcode\}"
ocodebeginmarkerE=r"\\begin\{lresult\}"
ocodendmarkerE=r"\\end\{lresult\}"
verbeginmarkerE=r"\%\\begin\{lresult\}"
verendmarkerE=r"\%\\end\{lresult\}"
inlinemarkerE=r"\\linline\{"
combeginmarkerE=r"\%lignore"
comendmarkerE=r"\%lnoignore"

allmarkersE='|'.join([icodebeginmarkerE,icodendmarkerE,
                      ocodebeginmarkerE,ocodendmarkerE,
                      verbeginmarkerE,verendmarkerE,
                      combeginmarkerE,comendmarkerE,
                      inlinemarkerE])
OBR="{"
CBR="}"
BCBR="\\}"
grammar_latex = fr"""
start: (topleveltext)? (snippet (topleveltext)? )*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | oversection -> e_versection
        | inlinesection -> e_inline
        | comsection -> e_comment
comsection.2 : combeginmarker comtext comendmarker
icodesection.1 : icodebeginmarker innertext icodendmarker
ocodesection.1 : ocodebeginmarker innertext ocodendmarker
oversection.1 : verbeginmarker innertext verendmarker
inlinesection.1 : inlinemarker "{OBR}" inltext "{CBR}" spaces_obr inltext cbr
inlinemarker : "{symbols_latex.inlinemarker}"
icodebeginmarker : "{symbols_latex.icodebeginmarker}"
icodendmarker : "{symbols_latex.icodendmarker}"
ocodebeginmarker : "{symbols_latex.ocodebeginmarker}"
ocodendmarker : "{symbols_latex.ocodendmarker}"
verbeginmarker : "{symbols_latex.verbeginmarker}"
verendmarker : "{symbols_latex.verendmarker}"
combeginmarker : "{symbols_latex.combeginmarker}"
comendmarker : "{symbols_latex.comendmarker}"
topleveltext : /(.(?!{allmarkersE}))*./s
innertext : /(.(?!{icodendmarkerE}|{ocodendmarkerE}|{verendmarkerE}))*./s
inltext : ( /(.(?!{CBR}))*./s )?
comtext : ( /(.(?!{comendmarkerE}))*./s )?
spaces_obr : /[ \t\r\n]*{OBR}/s
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

def eval_section_(a, tree, symbols, nsecs:Set[int]):
  if not running():
    start(a)
  ssrc:Dict[int,str]={}
  sres:Dict[int,str]={}
  class C(Interpreter):
    def __init__(self):
      self.nsec=-1
      self.nosec=0
    def text(self,tree):
      print(tree.children[0].value, end='')
    def topleveltext(self,tree):
      return self.text(tree)
    def innertext(self,tree):
      return self.text(tree)
    def icodesection(self,tree):
      self.nsec+=1
      self.nosec=0
      t=tree.children[1].children[0].value
      print(f"{symbols.icodebeginmarker}{t}{symbols.icodendmarker}", end='')
      bm,em=tree.children[0].meta,tree.children[2].meta
      t=unindent(bm.column-1,t)
      ssrc[self.nsec]=t
      if self.nsec in nsecs:
        sres[self.nsec]=process(t)
    def _result(self,tree,verbatim:bool):
      bmarker=symbols.verbeginmarker if verbatim else symbols.ocodebeginmarker
      emarker=symbols.verendmarker if verbatim else symbols.ocodendmarker
      bm,em=tree.children[0].meta,tree.children[2].meta
      if self.nsec in nsecs and self.nosec<1:
        assert self.nsec in sres
        # pstderr(f'executing {self.nsec}')
        print(bmarker + "\n" +
              indent(bm.column-1,(
              f"{sres[self.nsec]}"+
              emarker)),end='')
        self.nosec+=1
      else:
        # pstderr(f'skipping {self.nsec}')
        print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
    def ocodesection(self,tree):
      self._result(tree,verbatim=False)
    def oversection(self,tree):
      self._result(tree,verbatim=True)
    def inlinesection(self,tree):
      # pstderr(tree)
      self.nsec+=1
      bm,em=tree.children[0].meta,tree.children[4].meta
      code=tree.children[1].children[0].value
      spaces_obs=tree.children[2].children[0].value
      im=symbols.inlinemarker
      if self.nsec in nsecs:
        result=process('print('+code+');\n').rstrip('\n')
      else:
        result=tree.children[3].children[0].value if len(tree.children[3].children)>0 else ''
      print(f"{im}{OBR}{code}{CBR}{spaces_obs}{result}{CBR}", end='')
    def comsection(self,tree):
      bmarker=symbols.combeginmarker
      emarker=symbols.comendmarker
      print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
  C().visit(tree)

def solve_cpos(tree,cs:List[Tuple[int,int]]
               )->Tuple[int,Dict[Tuple[int,int],int]]:
  """ Solve the list of cursor positions into a set of section numbers. Also
  return the number of last section. """
  acc:dict={}
  class C(Interpreter):
    def __init__(self):
      self.nsec=-1
    def _count(self,bm,em):
      for (line,col) in cs:
        if cursor_within((line,col),(bm.line,bm.column),
                                    (em.end_line,em.end_column)):
          acc[(line,col)]=self.nsec
    def icodesection(self,tree):
      self.nsec+=1
      self._count(tree.children[0].meta,tree.children[2].meta)
    def ocodesection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
    def oversection(self,tree):
      self._count(tree.children[0].meta,tree.children[2].meta)
    def inlinesection(self,tree):
      self.nsec+=1
      self._count(tree.children[0].meta,tree.children[4].meta)
  c=C()
  c.visit(tree)
  return c.nsec,acc

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

def solve_sloc(s:str,tree)->Set[int]:
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
  # print(qs)
  nsec,nsol=solve_cpos(tree,list(nqueries.values()))
  nknown[lastq]=nsec
  def _get(q):
    return nsol[nqueries[q]] if q in nqueries else nknown[q]
  def _safeset(x):
    try:
      return set(x())
    except KeyError as err:
      pstderr(f"Unable to resolve section at {err}")
      return set()
  return set.union(*[_safeset(lambda:range(_get(q[0]),_get(q[1])+1)) if len(q)==2
                     else _safeset(lambda:[_get(q[0])]) for q in qs])

if __name__=='__main__':
  ap=ArgumentParser(prog='litrepl.py')
  ap.add_argument('--filetype',metavar='STR',default='markdown',help='ft help')
  ap.add_argument('--interpreter',metavar='EXE',default='auto',help='python|ipython|auto')
  sps=ap.add_subparsers(help='command help', dest='command')
  sps.add_parser('start',help='start help')
  sps.add_parser('start-ipython',help='start help')
  sps.add_parser('stop',help='stop help')
  sps.add_parser('parse',help='parse help')
  sps.add_parser('parse-print',help='parse-print help')
  apes=sps.add_parser('eval-section',help='eval-section help')
  apes.add_argument('--line',type=int,default=None)
  apes.add_argument('--col',type=int,default=None)
  eps=sps.add_parser('eval-sections',help='eval-sections help')
  eps.add_argument('locs',metavar='LOCS',default='*',help='locs help')
  sps.add_parser('repl',help='repl help')
  a=ap.parse_args(sys.argv[1:])

  if a.command=='start':
    start(a)
  elif a.command=='stop':
    stop()
  elif a.command=='parse':
    t=parse_(GRAMMARS[a.filetype])
    print(t.pretty())
  elif a.command=='parse-print':
    eval_section_(a,parse_(GRAMMARS[a.filetype]),SYMBOLS[a.filetype],{})
  elif a.command=='eval-section':
    t=parse_(GRAMMARS[a.filetype])
    nsecs=set(solve_cpos(t,[(a.line,a.col)])[1].values())
    eval_section_(a,t,SYMBOLS[a.filetype],nsecs)
  elif a.command=='eval-sections':
    t=parse_(GRAMMARS[a.filetype])
    nsecs=solve_sloc(a.locs,t)
    eval_section_(a,t,SYMBOLS[a.filetype],nsecs)
  elif a.command=='repl':
    system("socat - 'PIPE:_out.pipe,flock-ex-nb=1!!PIPE:_inp.pipe,flock-ex-nb=1'")
  else:
    pstderr(f'Unknown command: {a.command}')
    exit(1)

