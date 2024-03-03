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
if ! exists("g:litrepl_timeout")
  let g:litrepl_timeout = 0.5
endif

fun! LitReplCmd()
  return 'PATH='.g:litrepl_bin.':$PATH '.g:litrepl_exe.' --workdir='.expand('%:p:h')
endfun

fun! LitReplStart()
  execute '!'.LitReplCmd().' --interpreter='.g:litrepl_interpreter.' start'
endfun
command! -bar -nargs=0 LStart call LitReplStart()

fun! LitReplStop()
  execute '!'.LitReplCmd().' stop'
endfun
command! -bar -nargs=0 LStop call LitReplStop()

fun! LitReplRestart()
  execute '!'.LitReplCmd().' --interpreter='.g:litrepl_interpreter.' restart'
endfun
command! -bar -nargs=0 LRestart call LitReplRestart()

fun! LitReplParsePrint()
  execute '%!'.LitReplCmd().' parse-print'
endfun
command! -bar -nargs=0 LPP call LitReplParsePrint()

fun! LitReplTerm()
  execute "terminal ".LitReplCmd()." repl"
endfun
command! -bar -nargs=0 LTerm call LitReplTerm()

fun! LitReplOpenErr(file)
  if bufwinnr(a:file) <= 0
    execute "botright vs ".a:file
    execute "setlocal autoread"
  endif
endfun
command! -bar -nargs=0 LOpenErr call LitReplOpenErr(g:litrepl_errfile)

fun! LitReplVersion()
  echomsg systemlist(LitReplCmd()." --version")[0]
endfun
command! -bar -nargs=0 LVersion call LitReplVersion()

let g:litrepl_lastpos = "0:0"

fun! LitReplRun(command,timeout_initial,timeout_continue,pos)
  let ft = &filetype
  let cur = getcharpos('.')
  let cmd = a:command . " " . a:pos
  " A hack to remember the undo position
  execute "normal! I "
  execute "normal! x"
  " Execute the selected code blocks
  let cmdline = '%!'.LitReplCmd().
        \ ' --interpreter='.g:litrepl_interpreter.
        \ ' --timeout-initial='.a:timeout_initial.
        \ ' --timeout-continue='.a:timeout_continue.
        \ ' --debug='.g:litrepl_debug.
        \ ' --filetype='.ft.
        \ ' '.cmd.' 2>'.g:litrepl_errfile
  execute cmdline
  let errcode = v:shell_error
  call setcharpos('.',cur)
  if errcode != 0
    execute "u"
    call LitReplOpenErr(g:litrepl_errfile)
  else
    let g:litrepl_laspos = a:pos
    if g:litrepl_always_show_stderr != 0
      call LitReplOpenErr(g:litrepl_errfile)
    endif
  endif
endfun

fun! LitReplStatus()
  let ft = &filetype
  let cur = getcharpos('.')
  " A hack to remember the undo position
  execute "normal! I "
  execute "normal! x"
  " Execute the status command
  silent execute '%!'.LitReplCmd().
        \ ' --debug='.g:litrepl_debug.
        \ ' --filetype='.ft.
        \ ' status 2>'.g:litrepl_errfile.' >&2'
  call setcharpos('.',cur)
  execute "u"
  call LitReplOpenErr(g:litrepl_errfile)
endfun

fun! s:Pos(arg)
  if a:arg == ""
    let p = getcharpos('.')
    return p[1].":".p[2]
  else
    return a:arg
  endif
endfun

command! -bar -nargs=? LEval call LitReplRun("eval-sections", "inf", "inf", <SID>Pos(<q-args>))
command! -bar -nargs=? LEvalAsync call LitReplRun("eval-sections", g:litrepl_timeout, 0.0, <SID>Pos(<q-args>))
command! -bar -nargs=0 LEvalLast call LitReplRun("eval-sections", "inf", "inf", g:litrepl_lastcur)
command! -bar -nargs=? LEvalAbove call LitReplRun("eval-sections", "inf", "inf", "0..".<SID>Pos(<q-args>))
command! -bar -nargs=? LEvalBelow call LitReplRun("eval-sections", "inf", "inf", <SID>Pos(<q-args>)."..$")
command! -bar -nargs=0 LEvalAll call LitReplRun("eval-sections", "inf", "inf", "0..$")
command! -bar -nargs=? LInterrupt call LitReplRun("interrupt", 1.0, 1.0, <SID>Pos(<q-args>))

command! -bar -nargs=0 LStatus call LitReplStatus()

let g:litrepl_loaded = 1

