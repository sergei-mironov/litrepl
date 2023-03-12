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

~~~~ markdown
Executable sections are marked with either "python", "lpython" or "code" tags.
Putting the cursor on one of the typing the :LitEval1 command executes its code
in a background Python interpreter.

``` python
W='Hello, World!'
print(W)
```

Verbatim sections with "result" or "lresult" tags are the result sections . The
output of the code from the executable section is pasted there. The original
content of the section is replaced with the output of the last execution.

``` result
Hello, World!
```

Markdown comments taged with `code`/`nocode`/`result`/`noresult` also mark
executable and result sections. This way we could hide the executable code from
Markdown renderers and generate the markup they recognize.
markup.

<!-- code
print("Hello, LitREPL")
-->

<!-- result -->
Hello, LitREPL
<!-- noresult -->

<!-- result
Hello, LitREPL
-->
~~~~

### Converting to Jupyter Notebook

[Pandoc](https://pandoc.org) could be used to conver LitREPL-frinedly markdown
documents to the Jupyter Notebook format. In order make it recognize code and
result fields addtional efforts are required. Currently we aware of two options:
1. Mark Jupyter sections with fenced-div markup as described in the [Pandoc
   manual](https://pandoc.org/MANUAL.html#jupyter-notebooks)
   1. Consider the following Markdown `file.md`
      ````{.markdown}
      :::::: {.cell .code execution_count=1}
      ```python
      print("hello XXXXXXX")
      ```
      ::: {.output .stream .stdout}
      ```lresult
      hello XXXXXXX
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
      print("hello markdown")
      ```

      <div class="output stream stdout">
      ```lresult
      hello markdown
      ```
      </div>
      </div>
      ````
   2. Again, both `LitREPL` and `Pandoc` would recognize the format, plus most
      third-party renderers would ignore `div` tags. To convert this file to the
      Jupyter Notebook format, call pandoc with
      [native divs extension](https://pandoc.org/MANUAL.html#extension-native_divs)
      enabled
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

