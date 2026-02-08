#!/bin/sh

set -e

{
echo "# Contributing"

cat docs/development/common-scenarios.md | sed -n \
  '/BEGIN OF CONTRIBUTING.md/,/END OF CONTRIBUTING.md/{
    /BEGIN OF CONTRIBUTING.md/b
    /END OF CONTRIBUTING.md/b
    p }' | sed 's@../static/@./@'

echo "### More"
echo
echo "See the [development documentation](https://sergei-mironov.github.io/litrepl/development/#other-development-scenatios)"

} >CONTRIBUTING.md
