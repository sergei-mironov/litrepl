CWD=$(pwd)
export PATH=\
$CWD/sh:\
$CWD/python/bin:\
$PATH
export LITREPL_ROOT="$CWD"
export PYLIGHTNIX_ROOT="$CWD/_pylightnix"
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
python3 -c 'import dataclasses' || echo "Warning: 'dataclasses' python library not found" >&2
# python -c 'import pylightnix' || echo "Warning: 'lark' python library not found" >&2
litrepl --version >/dev/null || echo "litrepl is not in PATH" >&2
socat -V >/dev/null || echo "GNU socat not found" >&2
