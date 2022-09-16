if exists("g:litrepl_loaded")
  finish
endif
if ! exists("g:litrepl_bin")
  let g:litrepl_bin = expand('<sfile>:p:h:h').'/bin/'
endif
if ! exists("g:litrepl_exe")
  let g:litrepl_exe = 'litrepl'
endif
if ! exists("g:litrepl_always_show_stderr")
  let g:litrepl_always_show_stderr = 0
endif
if ! exists("g:litrepl_debug")
  let g:litrepl_debug = 0
endif
if ! exists("g:litrepl_errfile")
  let g:litrepl_errfile = '/tmp/litrepl.err'
endif
if ! exists("g:litrepl_interpreter")
  let g:litrepl_interpreter = 'auto'
endif
let $PATH=g:litrepl_bin.":".$PATH

fun! s:SessionStart()
  execute '!'.g:litrepl_exe.' --interpreter='.g:litrepl_interpreter.' start'
endfun
command! -nargs=0 LitStart call <SID>SessionStart()

fun! s:SessionStop()
  execute '!'.g:litrepl_exe.' stop'
endfun
command! -nargs=0 LitStop call <SID>SessionStop()

fun! s:SessionRestart()
  execute '!'.g:litrepl_exe.' restart'
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

fun! s:OpenErr(file)
  if bufwinnr(a:file) <= 0
    execute "botright vs ".a:file
    execute "setlocal autoread"
  endif
endfun
command! -nargs=0 LitOpenErr call <SID>OpenErr(g:litrepl_errfile)

fun! s:Version()
  echomsg systemlist(g:litrepl_exe." --version")[0]
endfun
command! -nargs=0 LitVersion call <SID>Version()

let g:litrepl_lastcur = [0,0,0,0]
fun! s:SessionEval(mode,timeout_initial,timeout_continue,p)
  let ft = &filetype
  let cur = getcharpos('.')
  let p = a:p
  let g:litrepl_lastcur = a:p
  if a:mode == 'Here'
    let cmd = "eval-sections '".p[1].":".p[2]."'"
  elseif a:mode == 'Int'
    let cmd = "interrupt '".p[1].":".p[2]."'"
  elseif a:mode == 'Above'
    let cmd = "eval-sections '0..".p[1].":".p[2]."'"
  elseif a:mode == 'Below'
    let cmd = "eval-sections '".p[1].":".p[2]."..$'"
  elseif a:mode == 'All'
    let cmd = "eval-sections '0..$'"
  else
    echomsg "Invalid mode '".a:mode."'"
    return
  end
  " A hack to remember the undo position
  execute "normal! I "
  execute "normal! x"
  " Execute the selected code blocks
  execute '%!'.g:litrepl_exe.
        \ ' --interpreter='.g:litrepl_interpreter.
        \ ' --timeout-initial='.a:timeout_initial.
        \ ' --timeout-continue='.a:timeout_continue.
        \ ' --debug='.g:litrepl_debug.
        \ ' --filetype='.ft.
        \ ' '.cmd.' 2>'.g:litrepl_errfile
  let errcode = v:shell_error
  call setcharpos('.',cur)
  if errcode != 0
    execute "u"
    call s:OpenErr(g:litrepl_errfile)
  else
    if g:litrepl_always_show_stderr != 0
      call s:OpenErr(g:litrepl_errfile)
    endif
  endif
endfun
command! -nargs=0 LitEval1 call <SID>SessionEval('Here',0.5,0.0,getcharpos('.'))
command! -nargs=0 LitEvalLast1 call <SID>SessionEval('Here',0.5,0.0,g:litrepl_lastcur)
command! -nargs=0 LitEvalWait1 call <SID>SessionEval('Here',"inf","inf",getcharpos('.'))
command! -nargs=0 LitEvalAbove call <SID>SessionEval("Above","inf","inf",getcharpos('.'))
command! -nargs=0 LitEvalBelow call <SID>SessionEval("Below","inf","inf",getcharpos('.'))
command! -nargs=0 LitEvalAll call <SID>SessionEval("All","inf","inf",getcharpos('.'))
command! -nargs=0 LitEvalBreak1 call <SID>SessionEval('Int',1.0,1.0,getcharpos('.'))

let g:litrepl_loaded = 1

