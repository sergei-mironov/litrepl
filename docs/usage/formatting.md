# Formatting
## Markdown

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


## Latex

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

