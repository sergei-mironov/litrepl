if exists("g:literepl_loaded")
  finish
endif
let g:literepl_loaded = 1

fun! s:SessionStart()
  execute "!literepl.py start"
endfun
command! -nargs=0 LitStart call <SID>SessionStart()

fun! s:SessionStop()
  execute "!literepl.py stop"
endfun
command! -nargs=0 LitStop call <SID>SessionStop()

fun! s:SessionParsePrint()
  execute "%! literepl.py parse-print"
endfun
command! -nargs=0 LitPP call <SID>SessionParsePrint()

fun! s:SessionEval1()
  let p = getcharpos('.')
  execute "%! literepl.py eval-section --line ".p[1]." --col ".p[2]." 2>/tmp/vim.err"
  if getfsize('/tmp/vim.err')>0
    for l in readfile('/tmp/vim.err')
      echomsg l
    endfor
  endif
  call setcharpos('.',p)
endfun
command! -nargs=0 LitEval1 call <SID>SessionEval1()


