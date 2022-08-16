if exists("g:litrepl_loaded")
  finish
endif
let g:litrepl_loaded = 1

fun! s:SessionStart()
  execute "!litrepl.py start"
endfun
command! -nargs=0 LitStart call <SID>SessionStart()

fun! s:SessionStop()
  execute "!litrepl.py stop"
endfun
command! -nargs=0 LitStop call <SID>SessionStop()

fun! s:SessionRestart()
  call s:SessionStop()
  call s:SessionStart()
endfun
command! -nargs=0 LitRestart call <SID>SessionRestart()

fun! s:SessionParsePrint()
  execute "%! litrepl.py parse-print"
endfun
command! -nargs=0 LitPP call <SID>SessionParsePrint()

fun! s:SessionRepl()
  execute "terminal litrepl.py repl"
endfun
command! -nargs=0 LitRepl call <SID>SessionRepl()

fun! s:SessionEval1()
  let p = getcharpos('.')
  execute "%! litrepl.py eval-section --line ".p[1]." --col ".p[2]." 2>/tmp/vim.err"
  if getfsize('/tmp/vim.err')>0
    for l in readfile('/tmp/vim.err')
      echomsg l
    endfor
  endif
  call setcharpos('.',p)
endfun
command! -nargs=0 LitEval1 call <SID>SessionEval1()


