import pytest
from lark import Lark
from textwrap import dedent
from litrepl.grammar import (
  SectionType,
  st2rule,
  SectionGrammar,
  markdown_sec,
  markdown_com_sec,
  latex_sec,
  secbody,
  mkgrammar,
  mk_markdown_grammar
)

def test_st2rule():
  # Test conversion of SectionType to rule
  assert st2rule(SectionType.Code) == "e_icodesection"
  assert st2rule(SectionType.Result) == "e_ocodesection"
  assert st2rule(SectionType.Ignore) == "e_comsection"

  # Test for unknown SectionType
  with pytest.raises(ValueError, match="Unknown section type"):
    st2rule(None)

def test_section_grammar():
  # Test SectionGrammar initialization
  sg = SectionGrammar(name='test', bmarker='begin', emarker='end', sectype=SectionType.Code)
  assert sg.name == 'test'
  assert sg.bmarker == 'begin'
  assert sg.emarker == 'end'
  assert sg.sectype == SectionType.Code

def test_markdown_sec():
  # Test markdown_sec function
  sg = markdown_sec('python')
  assert sg.name == 'python'
  assert sg.bmarker == '```[ ]*python'
  assert sg.emarker == '```'
  assert sg.sectype == SectionType.Code

def test_markdown_com_sec():
  # Test markdown_com_sec function
  sg = markdown_com_sec('tag')
  assert sg.name == 'comtag'
  assert sg.bmarker == '<!--[ ]*tag[ ]*-->'
  assert sg.emarker == '<!--[ ]*notag[ ]*-->'
  assert sg.sectype == SectionType.Code

def test_latex_sec():
  # Test latex_sec function
  sg = latex_sec('document')
  assert sg.name == 'document'
  assert sg.bmarker == '\\begin{document}'
  assert sg.emarker == '\\end{document}'
  assert sg.sectype == SectionType.Code

def test_secbody():
  sg = SectionGrammar('python', '```[ ]*python', '```', SectionType.Code)
  expected_output = dedent(f'''
  python: pythonbegin pythontext pythonend -> {st2rule(SectionType.Code)}
  pythonbegin: PYTHONBEGIN
  pythontext: /(.(?!```))*./s
  pythonend: PYTHONEND
  PYTHONBEGIN.2: /```[ ]*python/
  PYTHONEND.2: /```/
  ''')
  result = secbody(sg)
  assert result.strip() == expected_output.strip()

def test_mkgrammar():
  sg1 = SectionGrammar('python', '```[ ]*python', '```', SectionType.Code)
  sg2 = SectionGrammar('result', '```[ ]*result', '```', SectionType.Result)
  expected_output = dedent(f'''
  start: (topleveltext)? ((python|result) (topleveltext)?)*
  topleveltext : /(.(?!```[ ]*python|```[ ]*result))*./s


  python: pythonbegin pythontext pythonend -> {st2rule(SectionType.Code)}
  pythonbegin: PYTHONBEGIN
  pythontext: /(.(?!```))*./s
  pythonend: PYTHONEND
  PYTHONBEGIN.2: /```[ ]*python/
  PYTHONEND.2: /```/


  result: resultbegin resulttext resultend -> {st2rule(SectionType.Result)}
  resultbegin: RESULTBEGIN
  resulttext: /(.(?!```))*./s
  resultend: RESULTEND
  RESULTBEGIN.2: /```[ ]*result/
  RESULTEND.2: /```/
  ''')
  assert mkgrammar([sg1, sg2]).strip() == expected_output.strip()

def test_mk_markdown_grammar():
  # Test mk_markdown_grammar
  expected_output = mk_markdown_grammar(['javascript', 'html'])
  assert '```[ ]*python' in expected_output
  assert '```[ ]*javascript' in expected_output
  assert '```[ ]*html' in expected_output
  assert '<!--[ ]*ignore[ ]*-->' in expected_output

def test_parse_markdown():
  # Define a sample markdown document
  markdown_content = '''
  # Sample Document

  Below is a code block in Python:

  ```foo
  Foo section
  ```

  ```python
  print("Hello, World!")
  ```

  <!-- ignore -->

  This is a comment block that is ignored by the parser.

  <!-- noignore -->

  ```result
  Output of the code goes here.
  ```
  '''

  # Get the grammar from mk_markdown_grammar
  grammar = mk_markdown_grammar(['foo'])
  print(grammar)
  # Initialize the Lark parser
  parser = Lark(grammar, parser='earley', start='start', regex=True)
  # Attempt to parse the markdown document
  tree = parser.parse(markdown_content)
  # Check if parsed successfully by ensuring a tree is returned
  assert tree is not None
  print(tree)
  # Extract all the Tokens from the tree
  def _ntokens(n):
    return len(list(tree.find_data(n)))
  # Extract names from the tokens
  assert _ntokens('foobegin')>0, tree
  assert _ntokens('pythonbegin')>0, tree
  assert _ntokens('resultbegin')>0, tree



