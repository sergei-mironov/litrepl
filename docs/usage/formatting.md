# Formatting
## Markdown
### Basic syntax

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

#### Using fenced Markdown syntax extension

Mark Jupyter sections with fenced-div markup as described in the [Pandoc
manual](https://pandoc.org/MANUAL.html#jupyter-notebooks). Consider the
following `file.md`:

```` {.markdown}
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

The above format is recognized by both `Litrepl` and `Pandoc`, so to
convert it to the Jupyter Notebook format one may run:

```sh
$ pandoc file.md -o file.ipynb
```

Unfortunately, other renderers may interpret fenced divs incorrectly.

#### Using Native divs syntax extension

Alternatively, native divs syntax extension could be used. Consider the
following `file.md` file:

````
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

Both `Litrepl` and `Pandoc` will recognize this format, plus most third-party
renderers will ignore `div` tags. The downside of this approach is the fact that
pandoc now needs [native divs
extension](https://pandoc.org/MANUAL.html#extension-native_divs) to convert the
document:

```sh
$ pandoc -f markdown+native_divs file.md -o test.ipynb
```

## Latex

### Basic syntax

Litrepl treats `\begin{python}\end{python}` environment as code sections and
`\begin{result}\end{result}` environment as result sections. The names are
currently hardcoded into the simplified LitREPL parser. Wrapping it in other
tags is not allowed.

LaTeX does not know anything about these environments by default, so we need to
introduce these environments in the preamble:

``` tex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

\newenvironment{python}{\begin{texttt}}{\end{texttt}}
\newenvironment{result}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

\begin{document}
...
\end{document}
```

Executable sections is the document are enclosed with the `python` tags, results
- wtih `result` tags:

``` tex
\begin{python}
W='Hello, World!'
print(W)
\end{python}

\begin{result}
Hello, World!
\end{result}
```

LitREPL recognizes `result`/`noresult` LaTeX comments as result section markers.
This way we can use Python to emit LaTeX markup as output.

``` tex
%result
Hello, World!
%noresult
```

Additionally, LitREPL recognises `linline` 2-argument tags. The first arguement
is treated as a Python printable expression. The second arguemnt is an immediate
result section where the value of expression will be placed.

``` tex
\linline{W}{Hello, World!}
```

### In-PDF code highliting with Minted

The following Latex instructions can be used to properly highlight the code and
result sections. Note, that `pygmentize` system tool needs to be installed in
the system.

``` tex
\usepackage{minted}
\renewcommand{\MintedPygmentize}{pygmentize}

% LitREPL-compatible environment for Python code snippets
\newenvironment{python}
  {\VerbatimEnvironment
   \begin{minted}[autogobble,breaklines,fontsize=\footnotesize]{python}}
  {\end{minted}}
\BeforeBeginEnvironment{python}{\begin{mdframed}[nobreak=false,everyline=true]}
\AfterEndEnvironment{python}{\end{mdframed}}

% LitREPL-compatible ai secitons
\newenvironment{ai}
  {\vsp\textbf{User:}\vsp}
  {}
\newenvironment{airesult}
  {\vsp\textbf{AI:}\vsp}
  {}

% LitREPL-compatible environment for code results
\newenvironment{result}
  {\VerbatimEnvironment
   \begin{minted}[autogobble,breaklines,fontsize=\footnotesize]{text}}
  {\end{minted}}
\BeforeBeginEnvironment{result}{\begin{mdframed}[nobreak=true,frametitle=\tiny{Result}]}
\AfterEndEnvironment{result}{\end{mdframed}}

% LitREPL-compatible command for inline code results
\newcommand{\linline}[2]{#2}
\newcommand{\st}[1]{\sout{#1}}
\renewcommand{\t}[1]{\texttt{#1}}
```

Hint: Use `\usepackage[outputdir=_build]{minted}` if you specify a separate
build directory (here - `_build`). This workarounds a well-known Minted problem.

### Vim In-editor code highlighting with Vimtex

The following `.vimrc` Vimtex configuration enables highlighting of Python
code sections in LaTeX documents. We typically need to call these functions from
the `BufEnter` event handler.

``` vim
" .localvimrc
call vimtex#syntax#nested#include('python')
call vimtex#syntax#core#new_region_env('texLitreplZone', 'l[a-zA-Z0-9]*code',
  \ {'contains': '@vimtex_nested_python'})
```

