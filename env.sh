CWD=`pwd`
export PROJECT_SOURCE="$CWD"

export PATH=$CWD/sh:$CWD/python:$PATH
export PYLIGHTNIX_ROOT=$CWD/_pylightnix
export PYTHONPATH=\
$CWD/python:\
$CWD/modules/pylightnix/src:\
$PYTHONPATH
export MYPYPATH=\
$CWD/python:\
$CWD/modules/pylightnix/src
alias ipython="sh $CWD/ipython.sh"

unset vim
unset VIMRUNTIME

python3 -c 'import lark' || echo "Warning: 'lark' python library not found" >&2
# python -c 'import pylightnix' || echo "Warning: 'lark' python library not found" >&2
