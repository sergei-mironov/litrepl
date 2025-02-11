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
    SectionType.Code: "codesec",
    SectionType.Result: "resultsec",
    SectionType.Ignore: "ignoresec"
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
  return SectionGrammar(tag, r'```[ ]*l?%s|```[ ]*{[^}]*%s[^}]*}'%(tag,tag), '```', st)

def markdown_com_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(f'com{tag}', fr'<!--[ ]*l?{tag}[ ]*-->', fr'<!--[ ]*l?no{tag}[ ]*-->', st)

def latex_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(tag, r'\\begin{l?%s}'%(tag,), r'\\end{l?%s}'%(tag,), st)

def latex_com_sec(tag:str, st:SectionType=SectionType.Code)->SectionGrammar:
  return SectionGrammar(f'com{tag}', fr'\%[ ]*l?{tag}[ ]*\%', fr'\%[ ]*l?no{tag}[ ]*\%', st)

def secbody(sg:SectionGrammar)->str:
  return dedent(f'''
  {sg.name}: {sg.name}begin {sg.name}text {sg.name}end -> {st2rule(sg.sectype)}
  {sg.name}begin: {sg.name.upper()}BEGIN
  {sg.name}text: /(.(?!{sg.emarker}))*./s
  {sg.name}end: {sg.name.upper()}END
  {sg.name.upper()}BEGIN.2: /{sg.bmarker}/
  {sg.name.upper()}END.2: /{sg.emarker}/
  ''')

def mkgrammar(sgs:list[SectionGrammar], others:dict[str,tuple[str,str]]={}) -> str:
  bmarkers='|'.join([sg.bmarker for sg in sgs]+[str(v[0]) for v in others.values()])
  return '\n'.join([dedent(f'''
    start: (topleveltext)? (({'|'.join([sg.name for sg in sgs]+[str(k) for k in others.keys()])}) (topleveltext)?)*
    topleveltext : /(.(?!{bmarkers}))*./s
    '''),
    *[secbody(sg) for sg in sgs],
    *[str(v[1]) for v in others.values()],
  ])

def mk_markdown_grammar(tags:list[str]|None=None)->str:
  tags=tags or []
  code_sections=[
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
    *[latex_sec(tag, SectionType.Code) for tag in tags],
    *[latex_com_sec(tag, SectionType.Code) for tag in tags]
  ]
  other_sections=[
    latex_sec('result', SectionType.Result),
    latex_com_sec('result', SectionType.Result),
    latex_com_sec('ignore', SectionType.Ignore),
  ]

  OBR="{"
  CBR="}"
  inlinemarker=r'\\l?[a-zA-Z0-9]*inline'
  others = {'inline': (inlinemarker+"\\{", dedent(fr'''
  inline.1: inlinemarker "{OBR}" inltext "{CBR}" spaces obr inltext cbr -> inlinecodesec
  inlinemarker: /{inlinemarker}/
  inltext: ( /[^{OBR}{CBR}]+({OBR}[^{CBR}]*{CBR}[^{OBR}{CBR}]*)*/ )?
  spaces: ( /[ \t\r\n]+/s )?
  obr: "{OBR}"
  cbr: "{CBR}"
  '''))}
  return mkgrammar([*code_sections,*other_sections], others)


