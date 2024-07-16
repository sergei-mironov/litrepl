Formatting
==========


1. [Markdown](#markdown)
   * [Syntax](#syntax)
   * [Converting to Jupyter Notebook](#converting-to-jupyter-notebook)
2. [Latex](#latex)
   * [Syntax](#syntax)
   * [Python code highlighting](#python-code-highlighting)

Markdown
--------

### Syntax

Executable sections are verbatim sections marked with a number of tags,
including "python" and "code".

~~~~
``` python
W='Hello, World!'
print(W)
```
~~~~

Verbatim result sections might be marked as "result" or "lresult".

~~~~
``` result
Hello, World!
```
~~~~

Markdown comments taged with `python` and `result`/`noresult` (see an example
below) also mark executable and result sections. This syntax allows evaluation
of hidden blocks.

~~~~
<!-- python
print("Hello, LitREPL")
-->

<!-- result
Hello, LitREPL
-->

<!-- result -->
Hello, LitREPL
<!-- noresult -->
~~~~

The latter variant allows emitting parts of Markdown document.


### Converting to Jupyter Notebook

[Pandoc](https://pandoc.org) could be used to conver LitREPL-frinedly markdown
documents to the Jupyter Notebook format. In order to make it recognize the code
and result fields, addtional formatting is required. Currently we aware of two
options:

1. Mark Jupyter sections with fenced-div markup as described in the [Pandoc
   manual](https://pandoc.org/MANUAL.html#jupyter-notebooks)
   1. Consider the following Markdown `file.md`
      ````{.markdown}
      :::::: {.cell .code execution_count=1}
      ```python
      print("Hello Jupyter!")
      ```
      ::: {.output .stream .stdout}
      ``` result
      Hello Jupyter!
      ```
      :::
      ::::::
      ````
   2. The above format is recognized by both `LitREPL` and `Pandoc`, so to
      convert it to the Jupyter Notebook format one may run
      ```sh
      $ pandoc file.md -o file.ipynb
      ```
   3. Unfortunately, other renderers may interpret fenced divs incorrectly.

2. Alternatively, native divs could be used.
   1. Consider the following Markdown `file.md`
      ````{.markdown}
      <div class="cell code">
      ```python
      print("Hello Jupyter!")
      ```

      <div class="output stream stdout">
      ```result
      Hello Jupyter!
      ```
      </div>
      </div>
      ````
   2. Both `LitREPL` and `Pandoc` will recognize this format, plus most
      third-party renderers will ignore `div` tags. The downside of this
      approach is the fact that pandoc now needs [native divs
      extension](https://pandoc.org/MANUAL.html#extension-native_divs) to
      convert the document:
      ```sh
      $ pandoc -f markdown+native_divs test.md -o test.ipynb
      ```

Latex
-----

### Syntax

~~~~ latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

LitREPL treats \texttt{lcode} environment as code sections and \texttt{lresult}
environment as result sections. The names are currently hardcoded into the
simplified LitREPL parser. Wrapping it in other tags is not allowed.

LaTeX does not know anything about these environments by default, we need to
introduce them to be able to compile the document using e.g. \texttt{pdflatex}.

\newenvironment{lcode}{\begin{texttt}}{\end{texttt}}
\newenvironment{lresult}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

Executable section is the text between the \texttt{lcode} begin/end tags.

\begin{lcode}
W='Hello, World!'
print(W)
\end{lcode}

Putting the cursor on it and typing the \texttt{:LitEval1} runs the code in the
background Python interpreter.

\texttt{lresult} begin/end tags mark the result section.  LitREPL replaces its
content with the above code section's execution result.

\begin{lresult}
Hello, World!
\end{lresult}

LitREPL recognizes \texttt{l[no]code}/\texttt{l[no]result} comments as
code/result section markers. This way we can use Python to produce LaTeX markup
as output.

%lcode
print("Hi!")
%lnocode

%lresult
Hi!
%lnoresult

Additionally, VimREPL recognises \texttt{linline} 2-argument tags. The first
arguement is treaten as a Python printable expression. The second arguemnt is to
be replaced with the printing output. In our simplified definition, we simply
ignore the first argument and paste the second to the LaTeX processor as-is.

\linline{W}{Hello, World!}

\end{document}
~~~~

### Python code highlighting

The following `.vimrc` Vimtex configuration enables highlighting of Python
code sections in LaTeX documents. We typically need to call these functions from
the `BufEnter` event handler.

``` vim
" .localvimrc
call vimtex#syntax#nested#include('python')
call vimtex#syntax#core#new_region_env('texLitreplZone', 'l[a-zA-Z0-9]*code',
  \ {'contains': '@vimtex_nested_python'})
```

