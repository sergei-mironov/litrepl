#!/bin/sh
# Dumps the (a) command line; (b) Stdin; (c) Word 'END' to stdout and a file
{
echo $(basename "$0") "$@"
cat
echo END
} | tee _last_dummy_output.txt
