CWD=$(pwd)
export PROJECT_ROOT=$CWD
export PATH=\
$CWD/sh:\
$CWD/python/bin:\
$PATH
export LITREPL_ROOT="$CWD"
export PYTHONPATH=\
$CWD/python:\
$PYTHONPATH
export MYPYPATH=\
$CWD/python:\
alias ipython="sh $CWD/ipython.sh"

export ONDIRRC=`pwd`/.ondirrc

unset vim
unset VIMRUNTIME

python3 -c 'import lark' || echo "Warning: 'lark' python library not found" >&2
python3 -c 'import dataclasses' || echo "Warning: 'dataclasses' python library not found" >&2
litrepl --version >/dev/null || echo "litrepl is not in PATH" >&2
socat -V >/dev/null || echo "GNU socat not found" >&2

export LITREPL_PYTHON_AUXDIR=_litrepl/python
export LITREPL_AI_AUXDIR=_litrepl/ai
export LITREPL_SH_AUXDIR=_litrepl/sh
