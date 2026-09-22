
command! -bar -nargs=? LTangle execute "LPipeFile aicli-tangle.sh " . LitReplPos(<q-args>) . " - "
