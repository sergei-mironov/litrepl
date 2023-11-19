from textwrap import dedent
from re import match as re_match, compile as re_compile
from .types import CursorPos

def unindent(col:int, lines:str)->str:
  def _rmspaces(l):
    return l[col:] if l.startswith(' '*col) else l
  return '\n'.join(map(_rmspaces,lines.split('\n')))

def indent(col:int, lines:str)->str:
  return '\n'.join([' '*col+l for l in lines.split('\n')])

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

