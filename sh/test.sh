#!/bin/sh

mktest() {
  test -d "$LITREPL_ROOT"
  T="$LITREPL_ROOT/_test/$1"
  rm -rf  "$T" || true
  mkdir -p "$T"
  cd "$T"
}

test_parse_print() {( # {{{
mktest "_test_parse_print"
runlitrepl start
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
```lresult
Hello, LitREPL!
```
```python
hello("World")
```
```
Hello, World!
```
* List
* <!--lresult-->
  BLABLA
  <!--lnoresult-->
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
  %lresult
  hello("Verbose")
  %lnoresult
\end{itemize}
\end{document}
EOF

)} #}}}

test_eval_md() {( #{{{
mktest "_test_eval_md"
runlitrepl start
cat >source.md <<"EOF"
```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
```lresult
PLACEHOLDER
```
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
``` { .python }
print('Wowowou')
```
``` { .lresult }
PLACEHOLDER
```
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
* ```python
  print("ABC"+"DEF")
  ```
* <!--lresult-->
  PLACEHOLDER
  <!--lnoresult-->
== Ignore ==
<!--lignore-->
```python
print('A'+'B')
```
```
PLACEHOLDER
```
<!--lnoignore-->
```
NOEVAL
```
<!--result
EVAL
-->
<!--lcode
print('FOO')
lnocode-->
```lresult
XX
```
<!--code
print('BAR')
-->
<!--result-->
??
<!--noresult-->
``` code
print("-->")
```
<!-- result
??
-->
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
```lresult
Hello, World!
```
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
``` { .python }
print('Wowowou')
```
``` { .lresult }
Wowowou
```
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
* ```python
  print("ABC"+"DEF")
  ```
* <!--lresult-->
  ABCDEF
  <!--lnoresult-->
== Ignore ==
<!--lignore-->
```python
print('A'+'B')
```
```
PLACEHOLDER
```
<!--lnoignore-->
```
NOEVAL
```
<!--result
ABCDEF
-->
<!--lcode
print('FOO')
lnocode-->
```lresult
FOO
```
<!--code
print('BAR')
-->
<!--result-->
BAR
<!--noresult-->
``` code
print("-->")
```
<!-- result
\-\-\>
-->
EOF
runlitrepl stop
)} #}}}

test_eval_tex() {( #{{{
mktest "_test_eval_tex"
runlitrepl start
cat >source.tex <<"EOF"
% == Ignore non-tags ==
\newcommand{\linline}[2]{#2}
% == Normal evaluation ==
\begin{lcode}
print("A"+"B")
\end{lcode}
Text
\begin{enumerate}
\item
  %lresult
  PLACEHOLDER
  %lnoresult
\end{enumerate}
\begin{lresult}
PLACEHOLDER
\end{lresult}
% == Inline evaluation ==
\linline{"A"+"B"}
{XX}\linline{"C"+"D"}{}
\begin{lcode}
tag='\\textbf{bold}'
\end{lcode}
\linline{tag+tag}{\textbf{old}\textbf{old}}
% == Meta-comments ==
%lignore
\begin{lcode}
print("X"+"Y")
\end{lcode}
%lresult
ZZZZZ
%lnoresult
%lnoignore
\begin{lresult}
PLACEHOLDER
\end{lresult}
EOF
cat source.tex | runlitrepl --filetype=latex parse-print >out.tex
diff -u source.tex out.tex
cat source.tex | runlitrepl --filetype=latex eval-sections '0..$' >out.tex
diff -u out.tex - <<"EOF"
% == Ignore non-tags ==
\newcommand{\linline}[2]{#2}
% == Normal evaluation ==
\begin{lcode}
print("A"+"B")
\end{lcode}
Text
\begin{enumerate}
\item
  %lresult
  AB
  %lnoresult
\end{enumerate}
\begin{lresult}
AB
\end{lresult}
% == Inline evaluation ==
\linline{"A"+"B"}
{AB}\linline{"C"+"D"}{CD}
\begin{lcode}
tag='\\textbf{bold}'
\end{lcode}
\linline{tag+tag}{\textbf{bold}\textbf{bold}}
% == Meta-comments ==
%lignore
\begin{lcode}
print("X"+"Y")
\end{lcode}
%lresult
ZZZZZ
%lnoresult
%lnoignore
\begin{lresult}
\end{lresult}
EOF
runlitrepl stop
)} #}}}

test_eval_ignore() {( #{{{
mktest "_test_eval_ignore"
runlitrepl start
cat >source.tex <<"EOF"
\linline{"A"+"B"}
{XX}\linline{"C"+"D"}{}
\begin{lcode}
tag='\\textbf{bold}'
\end{lcode}
\linline{tag+tag}{\textbf{old}\textbf{old}}
\begin{lresult}
PLACEHOLDER
\end{lresult}
EOF
cat source.tex | runlitrepl --filetype=latex parse
cat source.tex | runlitrepl --filetype=latex parse-print >out.tex
diff -u source.tex out.tex
cat source.tex | runlitrepl --filetype=latex eval-sections '0..$' >out.tex
diff -u out.tex - <<"EOF"
\linline{"A"+"B"}
{AB}\linline{"C"+"D"}{CD}
\begin{lcode}
tag='\\textbf{bold}'
\end{lcode}
\linline{tag+tag}{\textbf{bold}\textbf{bold}}
EOF
runlitrepl stop
)} #}}}

test_tqdm() {( #{{{
mktest "_test_tqdm"
runlitrepl start
cat >source.md <<"EOF"
```python
from tqdm import tqdm
for i in tqdm(range(100)):
  pass
```
```lresult
```
EOF
cat source.md | runlitrepl --filetype=markdown parse-print >out.md
diff -u source.md out.md
cat source.md | runlitrepl --filetype=markdown eval-sections '0..$' >out.md
test "$(cat out.md | grep '100%' | wc -l)" = "1"
runlitrepl stop
)} #}}}

test_async() {( #{{{
mktest "_test_async"
runlitrepl start
cat >source.md <<"EOF"
```python
from tqdm import tqdm
from time import sleep
for i in tqdm(range(4)):
  sleep(1)
  pass
```
```lresult
```
EOF
cat source.md | runlitrepl --filetype=markdown --timeout-initial=1 eval-sections '0..$' >out1.md
cat out1.md | runlitrepl --filetype=markdown --timeout-continue=1 eval-sections '0..$' >out2.md
grep -q 'BG' out2.md
runlitrepl stop
)} #}}}

test_eval_code() {( #{{{
mktest "_test_eval_code"
runlitrepl start
cat >source.py <<"EOF"
def hello(name):
  print(f"Hello, {name}!")

hello('World')
EOF
cat source.py | runlitrepl eval-code >out.txt
diff -u out.txt - <<"EOF"
Hello, World!

EOF
runlitrepl stop
)} #}}}

interpreters() {
  echo "$(which python)"
  echo "$(which ipython)"
}

tests() {
  echo test_parse_print
  echo test_eval_md
  echo test_tqdm
  echo test_eval_tex
  echo test_async
  echo test_eval_code
}

runlitrepl() {
  test -n "$LITREPL_INTERPRETER"
  test -n "$LITREPL_BIN"
  $LITREPL_BIN --interpreter="$LITREPL_INTERPRETER" "$@"
}

set -e

INTERPS=`interpreters`
TESTS=`tests`
while test -n "$1" ; do
  case "$1" in
    -i) INTERPS="$2"; shift ;;
    --interpreters=*) INTERPS=$(echo "$1" | sed 's/.*=//g') ;;
    -t) TESTS="$2"; shift ;;
    --tests) TESTS=$(echo "$1" | sed 's/.*=//g') ;;
    -h|--help) echo "Usage: test.sh [-i I(,I)*] [-t T(,T)*]" >&1 ; exit 1 ;;
    -V|--verbose) set -x ;;
  esac
  shift
done

if test -z "$LITREPL_BIN"; then
  LITREPL_BIN=$LITREPL_ROOT/python/bin/litrepl
fi

trap "echo FAIL" EXIT
for t in $(tests) ; do
  for i in $(interpreters) ; do
    if echo "$INTERPS" | grep -q "$i" && \
       echo "$TESTS" | grep -q "$t" ; then

      echo "Running test '$t' interpreter '$i'"
      LITREPL_INTERPRETER="$i" $t
    fi
  done
done
trap "" EXIT
echo OK
