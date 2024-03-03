#!/bin/sh

mktest() {
  test -d "$LITREPL_ROOT"
  T="$LITREPL_ROOT/_test/$1"
  rm -rf  "$T" || true
  mkdir -p "$T"
  cd "$T"
  runlitrepl stop || true
  trap "runlitrepl stop" EXIT
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

test_eval_with_empty_lines() {( #{{{
mktest "_test_eval_with_empty_lines"
runlitrepl start
cat >source.py <<"EOF"
def hello():
  var = 33  # EMPTY LINE BELOW

  print(f"Hello, {var}!")

hello()
EOF
cat source.py | runlitrepl eval-code >out.txt
diff -u out.txt - <<"EOF"
Hello, 33!

EOF

cat >source.py <<"EOF"
def hello():
  try:
    var = 33  # EMPTY LINE BELOW

    print(f"Try-finally, {var}!")
  finally:
    print('Done')

hello()
EOF
cat source.py | runlitrepl eval-code >out.txt
diff -u out.txt - <<"EOF"
Try-finally, 33!
Done

EOF

cat >source.py <<"EOF"
if True:
    var = 33  # EMPTY LINE BELOW

    print(f"If-true, {var}!")
EOF
cat source.py | runlitrepl eval-code >out.txt
diff -u out.txt - <<"EOF"
If-true, 33!

EOF

cat >source.py <<"EOF"
def foo():
    def _bar():
      return 33

    print(_bar())

foo()
EOF
cat source.py | runlitrepl eval-code >out.txt
diff -u out.txt - <<"EOF"
33

EOF

# TODO: Re-enable when https://github.com/ipython/ipython/issues/14246 is fixed
if echo $LITREPL_INTERPRETER | grep -q ipython ; then
cat >source.py <<"EOF"
from textwrap import dedent
def foo():
  print(dedent('''
    aa

    bb
    ''').strip())
foo()
EOF
cat source.py | runlitrepl --debug=0 eval-code >out.txt
diff -u out.txt - <<"EOF"
aa

bb

EOF
fi

runlitrepl stop
)} #}}}

test_exit_errcode() {( #{{{
mktest "_test_exit_errcode"
runlitrepl start

cat >source.md <<"EOF"
``` python
print("before-exit")
```
``` result
```
``` python
import os
os._exit(123)
```
``` result
```

``` python
print("after-exit")
```
``` result
```
EOF
(
set +e
cat source.md | runlitrepl --filetype=markdown eval-sections '0..$' >out.md
echo $?>ret.txt
)
test `cat ret.txt` = "123"
grep -q "^before-exit" out.md
grep -q "123" out.md
grep -q -v "^after-exit" out.md
)} #}}}

test_exception_errcode() {( #{{{
mktest "_test_exception_errcode"
runlitrepl --exception-exit=123 start

cat >source.md <<"EOF"
``` python
print("before-exception")
```
``` result
```
``` python
raise Exception("exception")
```
``` result
```
``` python
print("after-exception")
```
``` result
```
EOF
(
set +e
cat source.md | runlitrepl --filetype=markdown eval-sections '0..$' >out.md
echo $?>ret.txt
)
test `cat ret.txt` = "123"
grep -q "^before-exception" out.md
grep -q "123" out.md
grep -q -v "^after-exception" out.md
runlitrepl stop
)} #}}}

test_print_system_order() {( #{{{
# See https://github.com/ipython/ipython/issues/14246
mktest "_test_eval_behavior"
runlitrepl start

cat >in.md <<"EOF"
``` python
from os import system
print("1")
_=system("echo 2")
```

``` result
```
EOF
cat in.md | runlitrepl --debug=0 --filetype=markdown eval-sections '0..$' >out.md
diff -u out.md - <<"EOF"
``` python
from os import system
print("1")
_=system("echo 2")
```

``` result
1
2
```
EOF

runlitrepl stop
)}
#}}}

test_vim_leval_cursor() {( #{{{
mktest "_test_vim_leval_cursor"

cat >file.md <<"EOF"
``` python
print("result-1")
```

``` result
```

``` python
print("result-2")
```

``` result
```
EOF

runvim file.md >_vim.log 2>&1 <<EOF
9G
:LEval
:wqa!
EOF
grep -q -v '^result-1' file.md
grep -q '^result-2' file.md
)}
#}}}

test_vim_leval_explicit() {( #{{{
mktest "_test_vim"

cat >file.md <<"EOF"
``` python
print("result-1")
```

``` result
```

``` python
print("result-2")
```

``` result
```
EOF

runvim file.md >_vim.log 2>&1 <<"EOF"
:LEval 1
:wq!
EOF
grep -q -v '^result-1' file.md
grep -q '^result-2' file.md

)}
#}}}

test_standalone_session() {( #{{{
mktest "_test_standalone_session"
runlitrepl start

cat >source.md <<"EOF"
``` python
session='common-session'
```
``` python
session='standalone-session'
```
``` python
print(session)
```
``` result
```
EOF
cat source.md | runlitrepl --filetype=markdown eval-sections '0,2' >out1.md
grep -q "^common-session" out1.md
cat source.md | runlitrepl --standalone-session --filetype=markdown eval-sections '1,2' >out2.md
grep -q "^standalone-session" out2.md
cat source.md | runlitrepl --filetype=markdown eval-sections '2' >out3.md
grep -q "^common-session" out3.md
)} #}}}

test_status() {( #{{{
mktest "_test_status"
runlitrepl status >status1.txt || true
grep -q '\?' status1.txt

cat >source.md <<"EOF"
``` python
var='value'
```
``` python
```
EOF
cat source.md | runlitrepl --filetype=markdown eval-sections '0..$' >out.md
runlitrepl status >status2.txt
grep -q -v '\?' status2.txt

)} #}}}

die() {
  echo "$@" >&2
  exit 1
}

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
  echo test_eval_with_empty_lines
  echo test_print_system_order
  echo test_exit_errcode
  echo test_exception_errcode
  echo test_vim_leval_cursor
  echo test_vim_leval_explicit
  echo test_standalone_session
  echo test_status
}

runlitrepl() {
  test -n "$LITREPL_INTERPRETER"
  test -n "$LITREPL_BIN"
  $LITREPL_BIN/litrepl --debug="$LITREPL_DEBUG" --interpreter="$LITREPL_INTERPRETER" "$@"
}

runvim() {
  {
    echo ":redir > _vim_messages.log"
    echo ":let g:litrepl_bin=\"$LITREPL_BIN\""
    echo ":let g:litrepl_interpreter=\"$LITREPL_INTERPRETER\""
    echo ":let g:litrepl_errfile='_litrepl.err'"
    cat
  } | \
  $LITREPL_ROOT/sh/vim_litrepl_dev "$@"
}

set -e

INTERPS=`interpreters`
TESTS=`tests`
LITREPL_DEBUG=0
while test -n "$1" ; do
  case "$1" in
    -i) INTERPS="$2"; shift ;;
    --interpreters=*) INTERPS=$(echo "$1" | sed 's/.*=//g') ;;
    -t) TESTS="$2"; shift ;;
    --tests) TESTS=$(echo "$1" | sed 's/.*=//g') ;;
    -h|--help) echo "Usage: test.sh [-i I(,I)*] [-t T(,T)*]" >&1 ; exit 1 ;;
    -d|-V|--verbose) set -x; LITREPL_DEBUG=1 ;;
  esac
  shift
done

if test "$INTERPS" = "?" ; then
  interpreters
fi
if test "$TESTS" = "?" ; then
  tests
fi
if test "$INTERPS" = "?" -o "$TESTS" = "?" ; then
  exit 1
fi

if test -z "$LITREPL_BIN"; then
  LITREPL_BIN=$LITREPL_ROOT/python/bin
fi

trap "echo FAIL" EXIT
NRUN=0
for t in $(tests) ; do
  for i in $(interpreters) ; do
    if echo "$INTERPS" | grep -q "$i" && \
       echo "$TESTS" | grep -q "$t" ; then

      echo "Running test \"$t\" interpreter \"$i\""
      LITREPL_INTERPRETER="$i" $t
      NRUN=$(expr $NRUN '+' 1)
    fi
  done
done
test $NRUN = 0 && die "No tests were run"
trap "" EXIT
echo OK
