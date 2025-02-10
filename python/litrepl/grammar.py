from textwrap import dedent
from dataclasses import dataclass
from enum import Enum

from enum import Enum

class SectionType(Enum):
  """ Sections types. `Ignore` are section-level block comments. """
  Code=0
  Result=1
  Ignore=2

def st2rule(st:SectionType)->str:
  rule_mapping = {
    SectionType.Code: "e_icodesection",
    SectionType.Result: "e_ocodesection",
    SectionType.Ignore: "e_comsection"
  }
  rule = rule_mapping.get(st)
  if rule is None:
    raise ValueError(f"Unknown section type {st}")
  return rule

@dataclass
class SectionGrammar:
  """ Section grammar parameters. """
  name:str
  bmarker:str
  emarker:str
  sectype:SectionType

def markdown_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(tag, f'```[ ]*{tag}', '```', st)

def markdown_com_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(f'com{tag}', f'<!--[ ]*{tag}[ ]*-->', f'<!--[ ]*no{tag}[ ]*-->', st)

def latex_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(tag, r'\\begin{%s}'%(tag,), r'\\end{%s}'%(tag,), st)

def latex_com_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(f'com{tag}', f'\%[ ]*{tag}[ ]*\%', f'\%[ ]*no{tag}[ ]*\%', st)

def secbody(sg:SectionGrammar)->str:
  return dedent(f'''
  {sg.name}: {sg.name}begin {sg.name}text {sg.name}end -> {st2rule(sg.sectype)}
  {sg.name}begin: {sg.name.upper()}BEGIN
  {sg.name}text: /(.(?!{sg.emarker}))*./s
  {sg.name}end: {sg.name.upper()}END
  {sg.name.upper()}BEGIN.2: /{sg.bmarker}/
  {sg.name.upper()}END.2: /{sg.emarker}/
  ''')

def mkgrammar(sgs:list[SectionGrammar]) -> str:
  bmarkers='|'.join([sg.bmarker for sg in sgs])
  return '\n'.join([dedent(f'''
    start: (topleveltext)? (({'|'.join([sg.name for sg in sgs])}) (topleveltext)?)*
    topleveltext : /(.(?!{bmarkers}))*./s
    '''),
    *[secbody(sg) for sg in sgs]
  ])

def mk_markdown_grammar(tags:list[str]|None=None)->str:
  tags=tags or []
  code_sections=[
    markdown_sec('python', SectionType.Code),
    markdown_com_sec('python', SectionType.Code),
    *[markdown_sec(tag, SectionType.Code) for tag in tags],
    *[markdown_com_sec(tag, SectionType.Code) for tag in tags]
  ]
  other_sections=[
    markdown_sec('result', SectionType.Result),
    markdown_com_sec('result', SectionType.Result),
    markdown_com_sec('ignore', SectionType.Ignore),
  ]
  return mkgrammar([*code_sections,*other_sections])

def mk_latex_grammar(tags:list[str]|None=None)->str:
  tags=tags or []
  code_sections=[
    latex_sec('python', SectionType.Code),
    latex_com_sec('python', SectionType.Code),
    *[latex_sec(tag, SectionType.Code) for tag in tags],
    *[latex_com_sec(tag, SectionType.Code) for tag in tags]
  ]
  other_sections=[
    latex_sec('result', SectionType.Result),
    latex_com_sec('result', SectionType.Result),
    latex_com_sec('ignore', SectionType.Ignore),
  ]
  return mkgrammar([*code_sections,*other_sections])


