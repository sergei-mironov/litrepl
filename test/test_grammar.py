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
  mk_markdown_grammar,
  mk_latex_grammar
)

def test_st2rule():
  # Test conversion of SectionType to rule
  assert st2rule(SectionType.Code) == "codesec"
  assert st2rule(SectionType.Result) == "resultsec"
  assert st2rule(SectionType.Ignore) == "ignoresec"

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
  assert 'python' in sg.bmarker
  assert sg.emarker == '```'
  assert sg.sectype == SectionType.Code

def test_markdown_com_sec():
  # Test markdown_com_sec function
  sg = markdown_com_sec('tag')
  assert sg.name == 'comtag'
  assert 'tag' in sg.bmarker
  assert 'tag' in sg.emarker
  assert sg.sectype == SectionType.Code

def test_latex_sec():
  # Test latex_sec function
  sg = latex_sec('document')
  assert sg.name == 'document'
  assert 'document' in sg.bmarker
  assert 'document' in sg.emarker
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
  expected_output = mk_markdown_grammar(['python', 'javascript', 'html'])
  assert '```[ ]*l?python' in expected_output
  assert '```[ ]*l?javascript' in expected_output
  assert '```[ ]*l?html' in expected_output
  assert '<!--[ ]*l?ignore[ ]*-->' in expected_output

def test_parse_markdown1():
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

  <!-- python -->
  print("Hello, World! (commented)")
  <!-- nopython -->

  <!-- ignore -->

  This is a comment block that is ignored by the parser.

  <!-- noignore -->

  ```result
  Output of the code goes here.
  ```
  '''

  # Get the grammar from mk_markdown_grammar
  grammar = mk_markdown_grammar(['python', 'foo'])
  print(grammar)
  # Initialize the Lark parser
  parser = Lark(grammar, parser='earley', start='start', regex=True)
  # Attempt to parse the markdown document
  tree = parser.parse(markdown_content)
  # Check if parsed successfully by ensuring a tree is returned
  assert tree is not None
  print(tree)
  # Extract tokens of a certain kind from the tree
  def _ntokens(n):
    return len(list(tree.find_data(n)))
  # Extract names from the tokens
  assert _ntokens('foobegin')>0, tree
  assert _ntokens('pythonbegin')>0, tree
  assert _ntokens('compythonbegin')>0, tree
  assert _ntokens('resultbegin')>0, tree

def test_parse_markdown2():
  # Define a sample markdown document
  markdown_content = '''
  Lorem Ipsum is simply dummy text of the printing and typesetting industry.

  ``` { .python }
  print('Wowowou')
  ```

  ``` { .lresult }
  Wowowou
  ```
  '''

  # Get the grammar from mk_markdown_grammar
  grammar = mk_markdown_grammar(['python'])
  print(grammar)
  # Initialize the Lark parser
  parser = Lark(grammar, propagate_positions=True)
  # Attempt to parse the markdown document
  tree = parser.parse(markdown_content)
  # Check if parsed successfully by ensuring a tree is returned
  assert tree is not None
  print(tree.pretty())
  # Extract tokens of a certain kind from the tree
  def _ntokens(n):
    return len(list(tree.find_data(n)))
  # Extract names from the tokens
  assert _ntokens('pythonbegin')>0, tree
  assert _ntokens('resultbegin')>0, tree


def test_parse_latex():
  latex_content = r'''
  % Sample Document

  Below is a code block in Python:

  \begin{foo}
  Foo section
  \end{foo}

  \begin{python}
  print("Hello, World!")
  \end{python}

  % python %
  print("Hello, World! (commented)")
  % nopython %

  % ignore %

  This is a comment block that is ignored by the parser.

  % noignore %

  \inline{var}{value}

  \begin{result}
  Output of the code goes here.
  \end{result}
  '''

  grammar = mk_latex_grammar(['python', 'foo'])
  print(grammar)
  parser = Lark(grammar, parser='earley', start='start', regex=True)
  tree = parser.parse(latex_content)
  assert tree is not None
  print(tree)

  def _ntokens(n):
    return len(list(tree.find_data(n)))

  assert _ntokens('foobegin')>0, tree
  assert _ntokens('pythonbegin')>0, tree
  assert _ntokens('compythonbegin')>0, tree
  assert _ntokens('resultbegin')>0, tree
  assert _ntokens('inlinemarker')>0, tree

