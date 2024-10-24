#!/bin/sh

mktest() {
  test -d "$LITREPL_ROOT"
  T="$LITREPL_ROOT/_test/$1"
  rm -rf  "$T" || true
  mkdir -p "$T"
  cd "$T"
  runlitrepl stop || true
  trap "runlitrepl stop || true" EXIT
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
<!--ai-->
AI MESSAGE
<!--noai-->
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
Simple evaluation
=================

```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
```lresult
PLACEHOLDER
```

Bracketed code sections
=======================

Lorem Ipsum is simply dummy text of the printing and typesetting industry.

``` { .python }
print('Wowowou')
```

``` { .lresult }
PLACEHOLDER
```

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor

Indent+Ignore
=============

The below part demonstrates 1) result indentation 2) ignored sections

* ```python
  print("ABC"+"DEF")
  ```
* <!--lresult-->
  PLACEHOLDER
  <!--lnoresult-->
  <!--lignore-->
  ```python
  print('A'+'B')
  ```
  ```
  PLACEHOLDER
  ```
  <!--lnoignore-->
  Just a verbatim section
  ```
  VERB
  ```
  Back the result section
  <!--
  ```result
  EVAL
  ```
  -->

Commented code section
======================

<!--
``` python
print('FOO')
```
-->
```lresult
XX
```
<!--result-->
??
<!--noresult-->

Stop tag protection
===================

``` code
print("<!-- noresult -->")
```
<!-- result -->
??
<!-- noresult -->

Inner markup safety
===================

``` python
print('`'+'`'+'`'+" vim \" Inner markup")
print('`'+'`'+'`')
```
<!--result-->
``` vim " Inner markup
```
<!--noresult-->
EOF
cat source.md | runlitrepl --filetype=markdown parse-print >out.md
diff -u source.md out.md
cat source.md | runlitrepl --filetype=markdown eval-sections >out.md
diff -u out.md - <<"EOF"
Simple evaluation
=================

```python
def hello(name):
  print(f"Hello, {name}!")

hello('World')
```
```lresult
Hello, World!
```

Bracketed code sections
=======================

Lorem Ipsum is simply dummy text of the printing and typesetting industry.

``` { .python }
print('Wowowou')
```

``` { .lresult }
Wowowou
```

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor

Indent+Ignore
=============

The below part demonstrates 1) result indentation 2) ignored sections

* ```python
  print("ABC"+"DEF")
  ```
* <!--lresult-->
  ABCDEF
  <!--lnoresult-->
  <!--lignore-->
  ```python
  print('A'+'B')
  ```
  ```
  PLACEHOLDER
  ```
  <!--lnoignore-->
  Just a verbatim section
  ```
  VERB
  ```
  Back the result section
  <!--
  ```result
  ABCDEF
  ```
  -->

Commented code section
======================

<!--
``` python
print('FOO')
```
-->
```lresult
FOO
```
<!--result-->
FOO
<!--noresult-->

Stop tag protection
===================

``` code
print("<!-- noresult -->")
```
<!-- result -->
\<\!\-\-\ \n\o\r\e\s\u\l\t\ \-\-\>
<!-- noresult -->

Inner markup safety
===================

``` python
print('`'+'`'+'`'+" vim \" Inner markup")
print('`'+'`'+'`')
```
<!--result-->
``` vim " Inner markup
```
<!--noresult-->
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
\begin{python}
print('FOOO')
\end{python}
%result
PLACEHOLDER
%noresult
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
\begin{python}
print('FOOO')
\end{python}
%result
FOOO
%noresult
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
cat source.md | runlitrepl --filetype=markdown --timeout=1,inf eval-sections >out1.md
cat out1.md | runlitrepl --filetype=markdown --timeout=inf,1 --pending-exit=33 eval-sections >out2.md ||
test "$?" = "33"
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
if echo $LITREPL_PYTHON_INTERPRETER | grep -q ipython ; then
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
not grep -q "^after-exit" out.md
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
not grep -q "^after-exception" out.md
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
runlitrepl start

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
not grep -q '^result-1' file.md
grep -q '^result-2' file.md
)}
#}}}

test_vim_leval_explicit() {( #{{{
mktest "_test_vim_leval_explicit"
runlitrepl start

cat >source.md <<"EOF"
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

``` python
print("result-3")
```

``` result
```
EOF

runvim >_vim.log 2>&1 <<"EOF"
:e! source.md
:LEval 1
:w! file1.md

:e! source.md
:LEval all
:w! file-all.md

:e! source.md
9G
:LEval above
:w! file-above.md

:e! source.md
9G
:LEval below
:w! file-below.md
:qa!
EOF

not grep -q '^result-1' file1.md
grep -q '^result-2' file1.md
not grep -q '^result-3' file1.md

grep -q '^result-1' file-all.md
grep -q '^result-2' file-all.md
grep -q '^result-3' file-all.md

grep -q '^result-1' file-above.md
grep -q '^result-2' file-above.md
not grep -q '^result-3' file-above.md

not grep -q '^result-1' file-below.md
grep -q '^result-2' file-below.md
grep -q '^result-3' file-below.md

)}
#}}}

test_vim_lmon() {( #{{{
mktest "_test_vim_lmon"
runlitrepl start

cat >file.md <<"EOF"
``` python
from time import sleep
for i in range(4):
  sleep(0.5)
  print(i, end='')

print()
```

``` result
```
EOF

runvim file.md >_vim.log 2>&1 <<"EOF"
:LEvalMon
:wq!
EOF
grep -q '0123' file.md
)}
#}}}

test_vim_lstatus() {( #{{{
mktest "_test_vim_lstatus"
runlitrepl start

runvim >_vim.log 2>&1 <<"EOF"
:let g:litrepl_errfile = '_litrepl.err'
:LStatus
:wqa!
EOF
not grep -q -i error _litrepl.err
)}
#}}}

test_vim_eval_selection() {( #{{{
mktest "_test_vim_eval_selection"
runlitrepl start

cat >file.md <<"EOF"
3 + 4
EOF

runvim file.md >_vim.log 2>&1 <<"EOF"
:vnoremap E :call LitReplEvalSelection('python')<CR>
VE
:wq!
EOF
grep -q '7' file.md
)}
#}}}

test_foreground() {( #{{{
mktest "_test_foreground"
runlitrepl start

cat >source.md <<"EOF"
``` python
session='common-session'
```
``` python
session='foreground'
```
``` python
print(session)
```
``` result
```
EOF
cat source.md | runlitrepl --filetype=markdown eval-sections '0,2' >out1.md
grep -q "^common-session" out1.md
cat source.md | runlitrepl \
  --foreground \
  --exception-exit=123 \
  --filetype=markdown \
  eval-sections '1,2' >out2.md
grep -q "^foreground" out2.md
cat source.md | runlitrepl --filetype=markdown eval-sections '2' >out3.md
grep -q "^common-session" out3.md
)} #}}}

test_status() {( #{{{
mktest "_test_status"
cat >source.md <<"EOF"
``` python
from time import sleep
while True:
  sleep(1)
```
``` result
```
EOF

runlitrepl stop
runlitrepl --verbose status python >status1.txt </dev/null || true
grep -q '?' status1.txt
cat source.md | runlitrepl \
  --filetype=markdown \
  --timeout=1,1 \
  eval-sections '0..$' >out.md
runlitrepl --verbose status python </dev/null >status2.txt
not grep -q '?' status2.txt
)} #}}}

test_interrupt() {( #{{{
mktest "_test_interrupt"
runlitrepl start
cat >source.md <<"EOF"
```python
from time import sleep
while True:
  sleep(1)
```
```result
```
EOF
cat source.md | runlitrepl \
  --filetype=markdown \
  --timeout=0,inf \
  eval-sections '0..$' >out1.md
grep -q 'BG' out1.md
sleep 1 # IPython seems to die without this delay
cat out1.md | runlitrepl \
  --filetype=markdown \
  interrupt '0..$' >out2.md

grep -q 'KeyboardInterrupt' out2.md
)} #}}}

test_invalid_interpreter() {( #{{{
# Exact result messages might start a race (exit code X VS broken pipe) That is
# why we put tow sections.
mktest "_test_invalid_interpreter"
cat >source.md <<"EOF"
```python
3+2
```
```result
```
```python
5+6
```
```result
```
EOF
cat source.md | runlitrepl --python-interpreter=non-existent-ipython \
  eval-sections >out1.md 2>err.txt || true
grep -q 'Interpreter exited with code: 127' out1.md
grep -q 'Interpreter exited with code: 127' err.txt
)} #}}}

test_aicli() {( #{{{
# Exact result messages might start a race (exit code X VS broken pipe) That is
# why we put tow sections.
mktest "_test_aicli"
runlitrepl start ai
cat >source.md <<"EOF"
```ai
/echo test
```
```result
```
EOF
cat source.md | runlitrepl eval-sections >out.md
diff -u out.md - <<"EOF"
```ai
/echo test
```
```result
test
ERROR: No model is active, use /model first
```
EOF
)} #}}}


die() {
  echo "$@" >&2
  exit 1
}

interpreters() {
  echo "$(which python)"
  echo "$(which ipython)"
}

not() {(
  set +e
  $@
  if test "$?" = "0" ; then
    exit 1
  else
    exit 0
  fi
)}

tests() {
  echo test_parse_print $(which python) -
  echo test_parse_print $(which ipython) -
  echo test_eval_md $(which python) -
  echo test_eval_md $(which ipython) -
  echo test_tqdm $(which python) -
  echo test_tqdm $(which ipython) -
  echo test_eval_tex $(which python) -
  echo test_eval_tex $(which ipython) -
  echo test_async $(which python) -
  echo test_async $(which ipython) -
  echo test_eval_code $(which python) -
  echo test_eval_code $(which ipython) -
  echo test_eval_with_empty_lines $(which python) -
  echo test_eval_with_empty_lines $(which ipython) -
  echo test_print_system_order $(which python) -
  echo test_print_system_order $(which ipython) -
  echo test_exit_errcode $(which python) -
  echo test_exit_errcode $(which ipython) -
  echo test_exception_errcode $(which python) -
  echo test_exception_errcode $(which ipython) -
  echo test_vim_leval_cursor $(which python) -
  echo test_vim_leval_cursor $(which ipython) -
  echo test_vim_leval_explicit $(which python) -
  echo test_vim_leval_explicit $(which ipython) -
  echo test_vim_lmon $(which python) -
  echo test_vim_lmon $(which ipython) -
  echo test_vim_lstatus $(which python) -
  echo test_vim_lstatus $(which ipython) -
  echo test_foreground $(which python) -
  echo test_foreground $(which ipython) -
  echo test_status $(which python) -
  echo test_status $(which ipython) -
  echo test_interrupt $(which python) -
  echo test_interrupt $(which ipython) -
  echo test_invalid_interpreter $(which python) -
  echo test_aicli - $(which aicli)
  echo test_vim_eval_selection $(which python) -
}

runlitrepl() {
  test -n "$LITREPL_PYTHON_INTERPRETER"
  test -n "$LITREPL_AI_INTERPRETER"
  test -n "$LITREPL_BIN"
  $LITREPL_BIN/litrepl --debug="$LITREPL_DEBUG" \
    --python-interpreter="$LITREPL_PYTHON_INTERPRETER" \
    --ai-interpreter="$LITREPL_AI_INTERPRETER" \
    "$@"
}

runvim() {
  {
    echo ":redir > _vim_messages.log"
    echo ":let g:litrepl_bin=\"$LITREPL_BIN\""
    echo ":let g:litrepl_python_interpreter=\"$LITREPL_PYTHON_INTERPRETER\""
    echo ":let g:litrepl_errfile='_litrepl.err'"
    cat
  } | \
  $LITREPL_ROOT/sh/vim_litrepl_dev --clean "$@"
}

set -e

export AICLI_NORC=y
INTERPS='.*'
TESTS='.*'
LITREPL_DEBUG=0
while test -n "$1" ; do
  case "$1" in
    --interpreters=*) INTERPS=$(echo "$1" | sed 's/.*=//g') ;;
    -i|--interpreters) INTERPS="$2"; shift ;;
    --tests=) TESTS=$(echo "$1" | sed 's/.*=//g') ;;
    -t|--tests) TESTS="$2"; shift ;;
    -h|--help) echo "Usage: test.sh [-i I(,I)*] [-t T(,T)*]" >&1 ; exit 1 ;;
    -d|-V|--verbose) set -x; LITREPL_DEBUG=1 ;;
  esac
  shift
done

if test "$TESTS" = "?" ; then
  tests | awk '{print $1}' | sort -u
fi
if test "$INTERPS" = "?" ; then
  tests | awk '{print $2}' | grep -v '-' | sort -u
  tests | awk '{print $3}' | grep -v '-' | sort -u
fi
if test "$INTERPS" = "?" -o "$TESTS" = "?" ; then
  exit 1
fi
if test -z "$LITREPL_BIN"; then
  LITREPL_BIN=$LITREPL_ROOT/python/bin
fi

trap "echo FAIL\(\$?\)" EXIT
tests | (
NRUN=0
while read t ipy iai ; do
  if echo "$t" | grep -q "$TESTS" && \
     ( echo "$ipy" | grep -q "$INTERPS" || \
       echo "$iai" | grep -q "$INTERPS" ; ) ; then
    echo "Running test \"$t\" python \"$ipy\" ai \"$iai\""
    NRUN=$(expr $NRUN '+' 1)
    LITREPL_PYTHON_INTERPRETER="$ipy" \
    LITREPL_AI_INTERPRETER="$iai" \
    $t
  fi
done
test "$NRUN" = "0" && die "No tests were run" || true
)
trap "" EXIT
echo OK

