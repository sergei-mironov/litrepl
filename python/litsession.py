#!/usr/bin/env python

from pylightnix import *
from typing import List, Optional
from re import search, match as re_match
import re
import os
import sys
from select import select
from os import environ, system
from lark import Lark, Visitor, Transformer, Token, Tree
from lark.visitors import Interpreter

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

def process():
  fdw=os.open('_inp.pipe', os.O_WRONLY | os.O_SYNC)
  fdr=os.open('_out.pipe', os.O_RDONLY | os.O_SYNC)
  lines=sys.stdin.readlines()
  res=interact(fdr,fdw,''.join(lines))
  print(res)

def start():
  system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('chmod -R +w _pylightnix 2>/dev/null && rm -rf _pylightnix')
  system('mkfifo _inp.pipe _out.pipe 2>/dev/null')
  if os.fork()==0:
    sys.stdout.close(); sys.stderr.close(); sys.stdin.close()
    system(('python -uic "import os; import sys; sys.ps1=\'\';'
            'os.open(\'_inp.pipe\',os.O_RDWR);'
            'os.open(\'_out.pipe\',os.O_RDWR);"'
            '<_inp.pipe >_out.pipe 2>&1 & echo $! >_pid.txt'))
    exit(0)

def stop():
  system('kill $(cat _pid.txt) >/dev/null 2>&1')
  system('rm _inp.pipe _out.pipe _pid.txt')


grammar_md = r"""
start: (snippet)*
snippet : icodesection -> e_icodesection
        | ocodesection -> e_ocodesection
        | inlinesection -> e_inline
        | osecmarker -> e_omarker
        | text -> e_text
icodesection.1 : "```" "python" text "```"
ocodesection.1 : "```" text "```"
inlinesection : "`" text "`"
text : /[^`]+/s
osecmarker : "`OUTPUT`"
"""

class MdPrinter(Interpreter):
  def text(self,tree):
    print(tree.children[0].value, end='')
  def icodesection(self,tree):
    print(f"```python{tree.children[0].children[0].value}```", end='')
  def ocodesection(self,tree):
    print(f"```{tree.children[0].children[0].value}```", end='')
  def inlinesection(self,tree):
    print(f"`{tree.children[0].children[0].value}`", end='')

def parse_md():
  parser = Lark(grammar_md)
  # print(parser)
  tree=parser.parse(sys.stdin.read())
  # print(tree.pretty())
  v=MdPrinter()
  v.visit(tree)


if __name__=='__main__':
  argv=sys.argv[1:]
  if any([a in ['start'] for a in argv]):
    start()
  elif any([a in ['stop'] for a in argv]):
    stop()
  elif any([a in ['eval'] for a in argv]):
    process()
  elif len(argv)==0 or any([a in ['parse-md'] for a in argv]):
    parse_md()
  else:
    print('Unknown command')

