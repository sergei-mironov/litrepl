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

Markdown comments tagged with `result`/`noresult` (see an example below) also
mark result sections. This syntax allows emitting parts of Markdown document.

~~~~
<!-- result -->
Hello, World!
<!-- noresult -->
~~~~


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

LitREPL treats `\begin{python}\end{python}` environment as code sections and
`\begin{result}\end{result}` environment as result sections. The names are
currently hardcoded into the simplified LitREPL parser. Wrapping it in other
tags is not allowed.

LaTeX does not know anything about these environments by default, so we need to
introduce these environments in the preamble:

~~~~ latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

\newenvironment{python}{\begin{texttt}}{\end{texttt}}
\newenvironment{result}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

\begin{document}
...
\end{document}
~~~~

Executable sections is the document are enclosed with the `python` tags, results
- wtih `result` tags:

~~~~

\begin{python}
W='Hello, World!'
print(W)
\end{python}

\begin{result}
Hello, World!
\end{result}

~~~~

LitREPL recognizes `result`/`noresult` LaTeX comments as result section markers.
This way we can use Python to emit LaTeX markup as output.

~~~~

%result
Hello, World!
%noresult

~~~~

Additionally, LitREPL recognises `linline` 2-argument tags. The first arguement
is treated as a Python printable expression. The second arguemnt is an immediate
result section where the value of expression will be placed.

~~~~
\linline{W}{Hello, World!}
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

