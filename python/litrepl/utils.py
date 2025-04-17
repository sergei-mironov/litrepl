from textwrap import dedent, wrap
from re import match as re_match, compile as re_compile
from typing import Iterable,List
from os import unlink, system
from hashlib import sha256
from .types import CursorPos

DEBUG:bool=False

def unindent(col:int, lines:str)->str:
  def _rmspaces(l):
    return l[col:] if l.startswith(' '*col) else l
  return '\n'.join(map(_rmspaces,lines.split('\n')))

def indent(col:int, lines:str)->str:
  """ Indent `lines` by addint `col` spaces to all non-empty line. The very last line is always
  indented. """
  ls=lines.split('\n')
  return '\n'.join([((' '*col+l) if (len(l)>0 or i==len(ls)-1) else '') for i,l in enumerate(ls)])

def escape(text, pat:str):
  """ Escapes every letter of a pattern with (\) """
  epat=''.join(['\\'+c for c in pat])
  return text.replace(pat,epat)


LEADSPACES=re_compile('^([ \t]*)')

def fillspaces(code:str, suffix:str)->str:
  """ Replace empty lines of a multi-line `code` with the lines filled with
  previous line's leading spaces, followed by `suffix` (typically a Python comment)."""
  def _leadspaces(line:str)->str:
    m=re_match(LEADSPACES,line)
    return str(m.group(1)) if m else ''
  lines=code.split('\n')
  if len(lines)<=0:
    return code
  acc=[lines[0]]
  nempty=0
  spaces=_leadspaces(lines[0])
  for line in lines[1:]:
    if len(line)==0:
      nempty+=1
    else:
      spaces2=_leadspaces(line)
      if nempty>0:
        acc.extend(['' if len(spaces2)==0 else spaces+suffix]*nempty)
        nempty=0
      acc.append(line)
      spaces=spaces2
  acc.extend(['']*nempty)
  return '\n'.join(acc)

def fmterror(s:str) -> str:
  return ' '.join(dedent(s).split('\n'))

def cursor_within(pos:CursorPos, posA:CursorPos, posB:CursorPos)->bool:
  if pos[0]>posA[0] and pos[0]<posB[0]:
    return True
  else:
    if pos[0]==posA[0]:
      return pos[1]>=posA[1]
    elif pos[0]==posB[0]:
      return pos[1]<posB[1]
    else:
      return False

def nlines(lines:str)->int:
  """ Return number of visual lines in `lines`. """
  return len(lines.split('\n'))


# def wraplong(lines:str, tw:int)->str:
#   """ Wrap long `lines`, preserve trailing newline"""
#   s='\n'.join(wrap(lines, width=tw))
#   s=s+'\n' if lines and lines[-1]=='\n' else s
#   return s
#

def words_with_spaces(text):
  word = ''
  for char in text:
    if char.isspace():
      if word:
        yield word
        word = ''
      word += char
    else:
      word += char
  if word and any((not c.isspace()) for c in word):
    yield word

def wraplong(lines:str, tw:int)->str:
  text, width = lines, tw
  wrapped_lines = []
  for line in text.split('\n'):
    if not line.strip():  # Check for empty lines
      wrapped_lines.append('')  # Preserve the empty line
      continue

    current_line = ""
    current_length = 0

    for word in words_with_spaces(line):
      if current_length + len(word) > width:
        if current_line != "":
          wrapped_lines.append(current_line)
        current_line = word.strip()
        current_length = len(word.strip())
      else:
        current_line += word
        current_length += len(word)

    if len(current_line) > 0:
      wrapped_lines.append(current_line)

  s = '\n'.join(wrapped_lines)
  s = s if len(lines)==0 or lines.endswith('\n') else s + '\n'
  return s

def remove_silent(f:str)->None:
  try:
    unlink(f)
  except FileNotFoundError:
    pass

SOCAT_HINT="Attaching to the interpreter (NO PROMPTS, USE `Ctrl+D` TO DETACH)\n"
def runsocat(fns, hint=None):
  if hint is None:
    hint=SOCAT_HINT
  print(hint,end='')
  system(f"socat - 'PIPE:{fns.outp},flock-ex-nb=1!!PIPE:{fns.inp},flock-ex-nb=1'")

def hashdigest(x)->str:
  return sha256(str(x).encode('utf-8')).hexdigest()[:7]

