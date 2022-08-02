CWD=`pwd`
export PROJECT_SOURCE="$CWD"

unset vim
export PATH=$CWD/sh:$PATH
export PYLIGHTNIX_ROOT=$CWD/_pylightnix
alias ipython="sh $CWD/ipython.sh"

unset VIMRUNTIME
# export VIMRUNTIME=`vim -e -T dumb --cmd 'exe "set t_cm=\<C-M>"|echo $VIMRUNTIME|quit' | tr -d '\015'`
# export VIMRUNTIME=$CWD/vim:$VIMRUNTIME
