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

fun! s:SessionEval(mode)
  let ft = &filetype
  let p = getcharpos('.')
  if a:mode == 'Here'
    let cmd = "'".p[1].":".p[2]."'"
  elseif a:mode == 'Above'
    let cmd = "'0..".p[1].":".p[2]."'"
  elseif a:mode == 'Below'
    let cmd = "'".p[1].":".p[2]."..$'"
  elseif a:mode == 'All'
    let cmd = "'0..$'"
  else
    echomsg "Invalid mode '".a:mode."'"
    return
  end
  " A hack to remember the undo position
  execute "normal! $i "
  execute "normal! a\<BS>"
  execute "%! litrepl.py --filetype=".ft." eval-sections ".cmd." 2>/tmp/vim.err"
  if getfsize('/tmp/vim.err')>0
    for l in readfile('/tmp/vim.err')
      echomsg l
    endfor
  endif
  call setcharpos('.',p)
endfun
command! -nargs=0 LitEval1 call <SID>SessionEval('Here')
command! -nargs=0 LitEvalAbove call <SID>SessionEval('Above')
command! -nargs=0 LitEvalBelow call <SID>SessionEval('Below')
command! -nargs=0 LitEvalAll call <SID>SessionEval('All')

