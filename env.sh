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
# export VIMRUNTIME=`vim -e -T dumb --cmd 'exe "set t_cm=\<C-M>"|echo $VIMRUNTIME|quit' | tr -d '\015'`
# export VIMRUNTIME=$CWD/vim:$VIMRUNTIME
