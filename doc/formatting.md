Formatting
----------

### Markdown

#### Syntax

````{.markdown}
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
````

#### Converting to Jupyter Notebook

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
   2. It is recognized by both `LitREPL` and `Pandoc`, so to convert it to the
      Jupyter Notebook format one may run
      ```sh
      $ pandoc file.md -o file.ipynb
      ```
   3. Unfortunately, other renderers may interpret fenced divs directly,
      bloating the output.

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

### Latex

#### Syntax

````latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

LitREPL for latex recognizes \texttt{lcode} environments as code and
\texttt{lresult} as result sections. The tag names is currently hardcoded into
the simple parser the tool is using, so we need to additionally introduce it to
the Latex system. Here we do it in a most simple way.

\newenvironment{lcode}{\begin{texttt}}{\end{texttt}}
\newenvironment{lresult}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

Executable section is the text between the \texttt{lcode} begin/end tags.
Putting the cursor on it and typing the \texttt{:LitEval1} executes it in the
background Python interpreter.

\begin{lcode}
W='Hello, World!'
print(W)
\end{lcode}

\texttt{lresult} tags next to the executable section mark the result section.
The output of the executable section will be pasted here. The
original content of the section will be replaced.

\begin{lresult}
Hello, World!
\end{lresult}

Commented \texttt{lresult}/\texttt{lnoresult} tags also marks result sections.
This way we could customise the Latex markup for every particular section.

\begin{lcode}
print("Hi!")
\end{lcode}

%lresult
Hi!
%lnoresult

Additionally, VimREPL for Latex recognises \texttt{linline} tags for which it
prints its first argument and pastes the result in place of the second argument.

\linline{W}{Hello, World!}

\end{document}
````

