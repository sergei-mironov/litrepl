#!/bin/sh

CWD=$(cd `dirname $0`/..; pwd;)

set -e -x

T="$CWD/_test"
rm -rf  "$T" || true
mkdir "$T"

for f in data/test-*md ; do
  d=$T/`basename "$f" .md`
  cat "$f" | litsession.py parse-print > "$d"
  diff -u "$f" "$d"
done
