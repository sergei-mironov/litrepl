#!/bin/sh

CWD=$(cd `dirname $0`/..; pwd;)

set -e -x

mktest() {
  T="$CWD/_test/$1"
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


test_eval_md_1() {
mktest "_test_eval_md_1"
runlitrepl start
runlitrepl eval-section --line 1 --col 1 >out.md <<"EOF"
```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
```
PLACEHOLDER
```
EOF
grep -q "Hello, World!" out.md
grep -v -q "PLACEHOLDER" out.md
runlitrepl stop
}

test_eval_md_2() {
mktest "_test_eval_md_2"
runlitrepl start
runlitrepl eval-section --line 1 --col 1 >out.md <<"EOF"
```python
print("ABC"+"DEF")
```
<!--litrepl-->
PLACEHOLDER
<!--litrepl-->
EOF
grep -q "ABCDEF" out.md
grep -v -q "PLACEHOLDER" out.md
runlitrepl stop
}

test_eval_tex_1() {
mktest "_test_eval_tex_1"
runlitrepl start
cat >source.tex <<"EOF"
\begin{lcode}
print("A"+"B")
\end{lcode}
Text
%\begin{lresult}
PLACEHOLDER
%\end{lresult}
EOF
cat source.tex | runlitrepl --filetype=latex eval-section --line 1 --col 1 >out.tex
grep -q "AB" out.tex
grep -v -q "PLACEHOLDER" out.tex
runlitrepl stop
}

trap "echo FAIL" EXIT
for I in python ipython ; do
  echo "Checking $I"
  LITREPL_INTERPRETER=$I
  test_parse_print
  test_eval_md_1
  test_eval_md_2
  test_eval_tex_1
done
trap "" EXIT
echo OK

