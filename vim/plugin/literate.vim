if exists("g:literate_loaded")
  finish
endif
let g:literate_loaded = 1
echomsg "Literate plugin is loading"

if !exists('g:literate_test')
  let g:literate_test = 1
endif

fun! s:SessionStart()
  execute "!litsession.py start"
endfun

fun! s:SessionStop()
  execute "!litsession.py stop"
endfun

command! -nargs=0 LitStart call <SID>SessionStart()
command! -nargs=0 LitStop call <SID>SessionStop()

