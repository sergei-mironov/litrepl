#!/bin/sh

CWD=$(cd `dirname $0`/..; pwd;)

set -e -x

mktest() {
  T="$CWD/_test/$1"
  rm -rf  "$T" || true
  mkdir -p "$T"
  cd "$T"
}

test_parsep_print() {(
mktest "_test_parse_print"
cp $CWD/data/test-*md .
for f in *md ; do
  cat "$f" | litrepl.py parse-print > "parsed_$f"
  diff -u "$f" "parsed_$f"
done
)}


test_eval1() {
mktest "_test_eval1"
litrepl.py start
litrepl.py eval-section --line 1 --col 1 >out.md <<"EOF"
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
litrepl.py stop
}

test_eval2() {
mktest "_test_eval2"
litrepl.py start
litrepl.py eval-section --line 1 --col 1 >out.md <<"EOF"
```python
print("ABC"+"DEF")
```
<!--litrepl-->
PLACEHOLDER
<!--litrepl-->
EOF
grep -q "ABCDEF" out.md
grep -v -q "PLACEHOLDER" out.md
litrepl.py stop
}

trap "echo FAIL" EXIT
test_parsep_print
test_eval1
test_eval2
trap "" EXIT
echo OK

