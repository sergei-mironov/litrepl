#!/bin/sh

mktest() {
  set -e -x
  test -d "$LITREPL_ROOT"
  T="$LITREPL_ROOT/_test/$1"
  rm -rf  "$T" || true
  mkdir -p "$T"
  cd "$T"
}

runlitrepl() {
  test -n "$LITREPL_INTERPRETER"
  litrepl.py --interpreter="$LITREPL_INTERPRETER" "$@"
}

test_parse_print() {( # {{{
mktest "_test_parse_print"
run_md() {
  cat > "source.md"
  cat "source.md" | runlitrepl --filetype=markdown parse-print > "parsed.md"
  diff -u "source.md" "parsed.md"
}
run_latex() {
  cat > "source.tex"
  cat "source.tex" | runlitrepl --filetype=latex parse-print > "parsed.tex"
  diff -u "source.tex" "parsed.tex"
}
run_md <<"EOF"
AAA
```python
def hello(name):
  print(f"Hello, {name}!")

hello("LitREPL")
```
```
Hello, LitREPL!
```
```python
hello("World")
```
```
Hello, World!
```
* List
* <!--litrepl-->
  BLABLA
  <!--litrepl-->
EOF

run_latex <<"EOF"
\documentclass{article}
\usepackage[utf8]{inputenc}
\newenvironment{lcode}{\begin{texttt}}{\end{texttt}}
\newenvironment{lresult}{\begin{texttt}}{\end{texttt}}

\begin{document}

\begin{lcode}
def hello(name):
  print(f"Hello, {name}!")

hello("LitREPL")
\end{lcode}

Footext

\begin{lresult}
????????
\end{lresult}

Bartext

\begin{itemize}
  \item
  \begin{lcode}
  hello("World")
  \end{lcode}

  \item Gootext

  \item
  \begin{lresult}
  ????????
  \end{lresult}

  \item
  \begin{lcode}
  hello("Verbose")
  \end{lcode}

  \item
  %\begin{lresult}
  hello("Verbose")
  %\end{lresult}
\end{itemize}
\end{document}
EOF

)} #}}}


test_eval_md() {(
mktest "_test_eval_md"
runlitrepl start
cat >source.md <<"EOF"
```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
TXT
```
PLACEHOLDER
```
TXT
* ```python
  print("ABC"+"DEF")
  ```
* <!--litrepl-->
  PLACEHOLDER
  <!--litrepl-->
EOF
cat source.md | runlitrepl --filetype=markdown parse-print >out.md
diff -u source.md out.md
cat source.md | runlitrepl --filetype=markdown eval-sections '0..$' >out.md
diff -u out.md - <<"EOF"
```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
TXT
```
Hello, World!
```
TXT
* ```python
  print("ABC"+"DEF")
  ```
* <!--litrepl-->
  ABCDEF
  <!--litrepl-->
EOF
runlitrepl stop
)}

test_eval_tex() {(
mktest "_test_eval_tex"
runlitrepl start
cat >source.tex <<"EOF"
\begin{lcode}
print("A"+"B")
\end{lcode}
Text
\begin{enumerate}
\item
  %\begin{lresult}
  PLACEHOLDER
  %\end{lresult}
\end{enumerate}
\begin{lresult}
NOEVAL
\end{lresult}
\linline{"A"+"B"}
{XX}\linline{"C"+"D"}{}
EOF
cat source.tex | runlitrepl --filetype=latex parse-print >out.tex
diff -u source.tex out.tex
cat source.tex | runlitrepl --filetype=latex eval-sections '0..$' >out.tex
diff -u out.tex - <<"EOF"
\begin{lcode}
print("A"+"B")
\end{lcode}
Text
\begin{enumerate}
\item
  %\begin{lresult}
  AB
  %\end{lresult}
\end{enumerate}
\begin{lresult}
NOEVAL
\end{lresult}
\linline{"A"+"B"}
{AB}\linline{"C"+"D"}{CD}
EOF
runlitrepl stop
)}

if test "$(basename $0)" = "test.sh" ; then
  set -e -x
  trap "echo FAIL" EXIT
  for I in python ipython ; do
    echo "Checking $I"
    LITREPL_INTERPRETER=$I
    test_parse_print
    test_eval_md
    test_eval_tex
  done
  trap "" EXIT
  echo OK
fi

