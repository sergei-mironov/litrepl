if exists("g:litrepl_loaded")
  finish
endif

if ! exists("g:litrepl_bin")
  let g:litrepl_bin = expand('<sfile>:p:h:h').'/bin/'
endif
if ! exists("g:litrepl_exe")
  let g:litrepl_exe = 'litrepl'
endif
let $PATH=g:litrepl_bin.":".$PATH


fun! s:SessionStart()
  execute '!'.g:litrepl_exe.' --interpreter=auto start'
endfun
command! -nargs=0 LitStart call <SID>SessionStart()

fun! s:SessionStop()
  execute '!'.g:litrepl_exe.' stop'
endfun
command! -nargs=0 LitStop call <SID>SessionStop()

fun! s:SessionRestart()
  call s:SessionStop()
  call s:SessionStart()
endfun
command! -nargs=0 LitRestart call <SID>SessionRestart()

fun! s:SessionParsePrint()
  execute '%!'.g:litrepl_exe.' parse-print'
endfun
command! -nargs=0 LitPP call <SID>SessionParsePrint()

fun! s:SessionRepl()
  execute "terminal ".g:litrepl_exe." repl"
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
  execute "normal! I "
  execute "normal! x"
  " Execute the selected code blocks
  let errfile = '/tmp/litrepl.err'
  execute '%!'.g:litrepl_exe.' --interpreter=auto --filetype='.ft.' eval-sections '.cmd.' 2>'.errfile
  let errcode = v:shell_error
  if getfsize('/tmp/vim.err')>0
    for l in readfile('/tmp/vim.err')
      echomsg l
    endfor
  endif
  call setcharpos('.',p)
  if errcode != 0
    execute "u"
    execute "botright vs ".errfile
  endif
endfun
command! -nargs=0 LitEval1 call <SID>SessionEval('Here')
command! -nargs=0 LitEvalAbove call <SID>SessionEval('Above')
command! -nargs=0 LitEvalBelow call <SID>SessionEval('Below')
command! -nargs=0 LitEvalAll call <SID>SessionEval('All')

let g:litrepl_loaded = 1

