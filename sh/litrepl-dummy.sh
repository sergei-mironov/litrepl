#!/bin/sh

{
echo $(basename "$0") "$@"
cat
echo END
} | tee _last_dummy_output.txt
