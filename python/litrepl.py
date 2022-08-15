#!/usr/bin/env python3

# from pylightnix import *

from typing import List, Optional
from re import search, match as re_match
import re
import os
import sys
from select import select
from os import environ, system
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter
from os.path import isfile
from signal import signal, SIGINT
from time import sleep

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
  fdw=os.open('_inp.pipe', os.O_WRONLY | os.O_SYNC)
  fdr=os.open('_out.pipe', os.O_RDONLY | os.O_SYNC)
  prev=None
  def _handler(signum,frame):
    os.kill(pid,SIGINT)
  prev=signal(SIGINT,_handler)
  try:
    return interact(fdr,fdw,lines)
  finally:
    signal(SIGINT,prev)
    os.close(fdr)
    os.close(fdw)

def start():
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
  return 0==system("test -f _pid.txt && test -p _inp.pipe && test -p _out.pipe")

def stop():
  system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('rm _inp.pipe _out.pipe _pid.txt')


grammar_md = r"""
start: (snippet)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | inlinesection -> e_inline
        | oversection -> e_versection
        | text -> e_text
icodesection.1 : codekbeginmarker "python" text codekendmarker
ocodesection.1 : codekbeginmarker text codekendmarker
oversection.1 : verbeginmarker text verendmarker
inlinesection : inlinebeginmarker text inlinendmarker
codekbeginmarker : "```"
codekendmarker : "```"
verbeginmarker : "<!--litrepl-->"
verendmarker : "<!--litrepl-->"
inlinebeginmarker : "`"
inlinendmarker : "`"
text : /(.(?!`|<\!--litrepl-->))*./s
"""
# text : /[^`]+/s

def parse_md():
  parser = Lark(grammar_md,propagate_positions=True)
  # print(parser)
  tree=parser.parse(sys.stdin.read())
  # print(tree.pretty())
  return tree


def print_md(tree):
  class C(Interpreter):
    def text(self,tree):
      print(tree.children[0].value, end='')
    def icodesection(self,tree):
      print(f"```python{tree.children[1].children[0].value}```", end='')
    def ocodesection(self,tree):
      print(f"```{tree.children[1].children[0].value}```", end='')
    def inlinesection(self,tree):
      print(f"`{tree.children[1].children[0].value}`", end='')
    def oversection(self,tree):
      print(f"<!--litrepl-->{tree.children[1].children[0].value}<!--litrepl-->", end='')
  C().visit(tree)


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

def eval_section(tree,line,col):
  if not running():
    start()
  class C(Interpreter):
    def __init__(self):
      self.task=None
      self.result=None
    def text(self,tree):
      print(tree.children[0].value, end='')
    def icodesection(self,tree):
      t=tree.children[1].children[0].value
      print(f"```python{t}```", end='')
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
      marker=f"<!--litrepl-->" if verbatim else "```"
      bm,em=tree.children[0].meta,tree.children[2].meta
      if self.result is None and \
         cursor_within((line,col),(bm.line,bm.column),
                       (em.end_line,em.end_column)) and \
         self.task is not None:
        self.result=process(self.task)
        self.task=None
      if self.result is not None:
        print(marker + "\n" +
              indent(bm.column-1,(
              f"{self.result}"+
              # f"============================\n"
              # f"cursor line {line} col {col}\n"
              marker)),end='')
        self.result=None
      else:
        print(f"{marker}{tree.children[1].children[0].value}{marker}", end='')
    def inlinesection(self,tree):
      print(f"`{tree.children[1].children[0].value}`", end='')
  C().visit(tree)

if __name__=='__main__':
  argv=sys.argv[1:]
  if any([a in ['start'] for a in argv]):
    start()
  elif any([a in ['stop'] for a in argv]):
    stop()
  # elif any([a in ['eval'] for a in argv]):
  #   print(process(''.join(sys.stdin.readlines())),end='')
  elif any([a in ['parse'] for a in argv]):
    t=parse_md()
    # print(t)
    print(t.pretty())
  elif any([a in ['parse-print'] for a in argv]):
    print_md(parse_md())
  elif any([a in ['eval-section'] for a in argv]):
    line=int(argv[argv.index('--line')+1])
    col=int(argv[argv.index('--col')+1])
    eval_section(parse_md(),line,col)
  elif any([a in ['repl'] for a in argv]):
    system("socat - 'PIPE:_out.pipe!!PIPE:_inp.pipe'")
  elif any([a in ['-h','--help'] for a in argv]):
    print('litrepl.py (start|stop|eval|parse-print|eval-section)')
  elif any([a in ['--version'] for a in argv]):
    print('litrepl.py development version')
  else:
    pstderr(f'Unknown arguments: {argv}')
    exit(1)

