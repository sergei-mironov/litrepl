#!/usr/bin/env python3

# from pylightnix import *

from typing import List, Optional, Tuple
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

def start():
  """ Starts the background Python interpreter. Kill an existing interpreter if
  any. Creates files `_inp.pipe`, `_out.pipt`, `_pid.txt`."""
  if isfile('_pid.txt'):
    system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('chmod -R +w _pylightnix 2>/dev/null && rm -rf _pylightnix')
  system('mkfifo _inp.pipe _out.pipe 2>/dev/null')
  if os.fork()==0:
    sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    system(('python -uic "import os; import sys; sys.ps1=\'\'; sys.ps2=\'\';'
            'os.open(\'_inp.pipe\',os.O_RDWR);'
            'os.open(\'_out.pipe\',os.O_RDWR);"'
            '<_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
    open('_inp.pipe','w').write(
      'import signal\n'
      'def _handler(signum,frame):\n'
      '  raise KeyboardInterrupt()\n\n'
      '_=signal.signal(signal.SIGINT,_handler)\n')
    exit(0)
  else:
    for i in range(10):
      if isfile("_pid.txt"):
        break
      sleep(0.5)
    if not isfile("_pid.txt"):
      raise ValueError("Couldn't see '_pid.txt'. Did the fork fail?")

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

symbols_md=SymbolsMarkdown()

grammar_md = fr"""
start: (snippet)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | oversection -> e_versection
        | text -> e_text
//        | inlinesection -> e_inline
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
text : /(.(?!```|<\!--litrepl-->))*./s
"""


@dataclass
class SymbolsLatex:
  icodebeginmarker=r"\begin{lcode}"
  icodendmarker=r"\end{lcode}"
  ocodebeginmarker=r"\begin{lresult}"
  ocodendmarker=r"\end{lresult}"
  verbeginmarker=r"%\begin{lresult}"
  verendmarker=r"%\end{lresult}"

symbols_latex=SymbolsLatex()
icodebeginmarkerE=r"\\begin\{lcode\}"
icodendmarkerE=r"\\end\{lcode\}"
ocodebeginmarkerE=r"\\begin\{lresult\}"
ocodendmarkerE=r"\\end\{lresult\}"
verbeginmarkerE=r"\%\\begin\{lresult\}"
verendmarkerE=r"\%\\end\{lresult\}"

grammar_latex = fr"""
start: (snippet)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | oversection -> e_versection
        | topleveltext -> e_text
        // | inlinesection -> e_inline
icodesection.1 : icodebeginmarker innertext icodendmarker
ocodesection.1 : ocodebeginmarker innertext ocodendmarker
oversection.1 : verbeginmarker innertext verendmarker
icodebeginmarker : "{symbols_latex.icodebeginmarker}"
icodendmarker : "{symbols_latex.icodendmarker}"
ocodebeginmarker : "{symbols_latex.ocodebeginmarker}"
ocodendmarker : "{symbols_latex.ocodendmarker}"
verbeginmarker : "{symbols_latex.verbeginmarker}"
verendmarker : "{symbols_latex.verendmarker}"
topleveltext : /(.(?!{icodebeginmarkerE}|{ocodebeginmarkerE}|{verbeginmarkerE}))*./s
innertext : /(.(?!{icodendmarkerE}|{ocodendmarkerE}|{verendmarkerE}))*./s
"""

def parse_(grammar):
  parser = Lark(grammar,propagate_positions=True)
  # print(parser)
  tree=parser.parse(sys.stdin.read())
  # print(tree.pretty())
  return tree

GRAMMARS={'markdown':grammar_md,'latex':grammar_latex}

def parse_md():
  return parse_(grammar_md)
def parse_latex():
  return parse_(grammar_latex)

def print_(tree,symbols):
  class C(Interpreter):
    def text(self,tree):
      print(tree.children[0].value, end='')
    def icodesection(self,tree):
      print(f"{symbols.icodebeginmarker}{tree.children[1].children[0].value}{symbols.icodendmarker}", end='')
    def ocodesection(self,tree):
      print(f"{symbols.ocodebeginmarker}{tree.children[1].children[0].value}{symbols.ocodendmarker}", end='')
    # def inlinesection(self,tree):
    #   print(f"`{tree.children[1].children[0].value}`", end='')
    def oversection(self,tree):
      print(f"{symbols.verbeginmarker}{tree.children[1].children[0].value}{symbols.verendmarker}", end='')
  C().visit(tree)

print_md=partial(print_,symbols=symbols_md)
print_latex=partial(print_,symbols=symbols_latex)
SYMBOLS={'markdown':symbols_md,'latex':symbols_latex}

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

def eval_section_(tree, symbols, cpos:Optional[Tuple[int,int]]=None,
                  nsec:Optional[int]=None):
  # TODO: nsec
  assert cpos is not None
  line,col=cpos if cpos is not None else (None,None)
  if not running():
    start()
  class C(Interpreter):
    def __init__(self):
      self.task=None
      self.result=None
    def text(self,tree):
      print(tree.children[0].value, end='')
    def topleveltext(self,tree):
      return self.text(tree)
    def innertext(self,tree):
      return self.text(tree)
    def icodesection(self,tree):
      t=tree.children[1].children[0].value
      print(f"{symbols.icodebeginmarker}{t}{symbols.icodendmarker}", end='')
      bm,em=tree.children[0].meta,tree.children[2].meta
      self.task=unindent(bm.column-1,t)
      self.result=None
      if cursor_within((line,col),(bm.line,bm.column),
                       (em.end_line,em.end_column)):
        self.result=process(self.task)
    def ocodesection(self,tree):
      self._result(tree,verbatim=False)
    def oversection(self,tree):
      self._result(tree,verbatim=True)
    def _result(self,tree,verbatim:bool):
      bmarker=symbols.verbeginmarker if verbatim else symbols.ocodebeginmarker
      emarker=symbols.verendmarker if verbatim else symbols.ocodendmarker
      bm,em=tree.children[0].meta,tree.children[2].meta
      if self.result is None and \
         cursor_within((line,col),(bm.line,bm.column),
                       (em.end_line,em.end_column)) and \
         self.task is not None:
        self.result=process(self.task)
        self.task=None
      if self.result is not None:
        print(bmarker + "\n" +
              indent(bm.column-1,(
              f"{self.result}"+
              # f"============================\n"
              # f"cursor line {line} col {col}\n"
              emarker)),end='')
        self.result=None
      else:
        print(f"{bmarker}{tree.children[1].children[0].value}{emarker}", end='')
    # def inlinesection(self,tree):
    #   print(f"`{tree.children[1].children[0].value}`", end='')
  C().visit(tree)

eval_section_md=partial(eval_section_,symbols=symbols_md)
eval_section_latex=partial(eval_section_,symbols=symbols_latex)

if __name__=='__main__':
  argv=sys.argv[1:]
  ap=ArgumentParser(prog='litrepl.py')
  ap.add_argument('--filetype',metavar='STR',default='markdown',help='ft help')
  sps=ap.add_subparsers(help='command help', dest='command')
  sps.add_parser('start',help='start help')
  sps.add_parser('stop',help='stop help')
  sps.add_parser('parse',help='parse help')
  sps.add_parser('parse-print',help='parse-print help')
  apes=sps.add_parser('eval-section',help='eval-section help')
  apes.add_argument('--line',type=int,default=None)
  apes.add_argument('--col',type=int,default=None)
  apes.add_argument('--nsec',type=int,default=None)
  sps.add_parser('repl',help='repl help')
  a=ap.parse_args(argv)

  if a.command=='start':
    start()
  elif a.command=='stop':
    stop()
  elif a.command=='parse':
    t=parse_(GRAMMARS[a.filetype])
    print(t.pretty())
  elif a.command=='parse-print':
    print_(parse_(GRAMMARS[a.filetype]),SYMBOLS[a.filetype])
  elif a.command=='eval-section':
    cpos=(a.line,a.col) if None not in [a.line,a.col] else None
    eval_section_(parse_(GRAMMARS[a.filetype]),SYMBOLS[a.filetype],cpos,a.nsec)
  elif a.command=='repl':
    system("socat - 'PIPE:_out.pipe,flock-ex-nb=1!!PIPE:_inp.pipe,flock-ex-nb=1'")
  else:
    pstderr(f'Unknown command: {a.command}')
    exit(1)

