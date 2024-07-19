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
if ! exists("g:litrepl_map_cursor_output")
  " No `:` are allowed in the file name
  let g:litrepl_map_cursor_output = '/tmp/litrepl_cursor.txt'
endif
if ! exists("g:litrepl_python_interpreter")
  let g:litrepl_python_interpreter = 'auto'
endif
if ! exists("g:litrepl_ai_interpreter")
  let g:litrepl_ai_interpreter = 'auto'
endif
if ! exists("g:litrepl_timeout")
  let g:litrepl_timeout = 0.5
endif
if ! exists("g:litrepl_pending")
  let g:litrepl_pending = 33
endif

fun! LitReplCmd()
  return 'PATH='.g:litrepl_bin.':$PATH '.g:litrepl_exe.' --workdir='.expand('%:p:h')
endfun

fun! LitReplStart(what)
  execute '!'.LitReplCmd().
        \' --python-interpreter="'.g:litrepl_python_interpreter.'"'.
        \' --ai-interpreter="'.g:litrepl_ai_interpreter.'"'.
        \' start '.a:what
endfun
command! -bar -nargs=? LStart call LitReplStart(<q-args>)

fun! LitReplStop(what)
  execute '!'.LitReplCmd().' stop '.a:what
endfun
command! -bar -nargs=? LStop call LitReplStop(<q-args>)

fun! LitReplRestart(what)
  execute '!'.LitReplCmd().
        \' --python-interpreter="'.g:litrepl_python_interpreter.'"'.
        \' --ai-interpreter="'.g:litrepl_ai_interpreter.'"'.
        \' restart '.a:what
endfun
command! -bar -nargs=? LRestart call LitReplRestart(<q-args>)

fun! LitReplParsePrint()
  execute '%!'.LitReplCmd().' parse-print'
endfun
command! -bar -nargs=0 LPP call LitReplParsePrint()

fun! LitReplTerm(what)
  execute "terminal ".LitReplCmd()." repl ".a:what
endfun
command! -bar -nargs=? LTerm call LitReplTerm(<q-args>)

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

fun! LitReplUpdateCursor(cur)
  let cur = a:cur
  let newrow = str2nr(readfile(g:litrepl_map_cursor_output)[0])
  if newrow != 0
    let cur[1] = newrow
  endif
  call setcharpos('.',cur)
endfun

fun! LitReplRun_(command, timeout, pos)
  let ft = &filetype
  let cur = getcharpos('.')
  let cmd_pos = a:command . " " . a:pos
  " Open a new undo block
  let &ul=&ul
  " Execute the selected code blocks
  let cmdline = '%!'.LitReplCmd().
        \ ' --python-interpreter="'.g:litrepl_python_interpreter.'"'.
        \ ' --ai-interpreter="'.g:litrepl_ai_interpreter.'"'.
        \ ' --timeout='.a:timeout.
        \ ' --pending-exit='.g:litrepl_pending.
        \ ' --debug='.g:litrepl_debug.
        \ ' --filetype='.ft.
        \ ' --map-cursor='.cur[1].':'.cur[2].':'.g:litrepl_map_cursor_output.
        \ ' --result-textwidth='.string(&textwidth).
        \ ' '.cmd_pos.' 2>'.g:litrepl_errfile
  silent execute cmdline
  call LitReplUpdateCursor(cur)
  return v:shell_error
endfun

fun! LitReplRun(command, timeout, pos)
  let cur = getcharpos('.')
  let command = '--propagate-sigint ' . a:command
  let errcode = LitReplRun_(command, a:timeout, a:pos)
  if errcode == 0 || errcode == g:litrepl_pending
    let g:litrepl_laspos = a:pos
    if errcode == 0
      if g:litrepl_always_show_stderr != 0
        call LitReplOpenErr(g:litrepl_errfile)
      endif
      return 0
    else
      return 1
    endif
  else
    execute "u"
      call LitReplUpdateCursor(cur)
    call LitReplOpenErr(g:litrepl_errfile)
    return 0
  endif
endfun

" Continuosly run litrepl until error or completion
fun! LitReplMonitor(command, pos)
  let cur = getcharpos('.')
  try
    while 1
      let code = LitReplRun_(a:command, g:litrepl_timeout.',0.0', a:pos)
      if code == 0
        call LitReplUpdateCursor(cur)
        break
      elseif code != g:litrepl_pending
        execute "u"
        call LitReplUpdateCursor(cur)
        break
      endif
      silent execute "redraw"
    endwhile
  catch /Vim:Interrupt/
    call LitReplUpdateCursor(cur)
  endtry
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
        \ ' --verbose'.
        \ ' status 2>'.g:litrepl_errfile.' >&2'
  call setcharpos('.',cur)
  execute "u"
  call LitReplOpenErr(g:litrepl_errfile)
endfun

fun! s:Pos(arg)
  let p = getcharpos('.')
  let loc = p[1].":".p[2]
  if a:arg == ""
    return loc
  elseif tolower(a:arg) == "all"
    return "0..$"
  elseif tolower(a:arg) == "above"
    return "0..".loc
  elseif tolower(a:arg) == "below"
    return loc."..$"
  else
    return a:arg
  endif
endfun

command! -bar -nargs=? LEval call LitReplRun("eval-sections", "inf,inf", <SID>Pos(<q-args>))
command! -bar -nargs=? LEvalAsync call LitReplRun("eval-sections", g:litrepl_timeout.',0.0', <SID>Pos(<q-args>))
command! -bar -nargs=? LEvalMon call LitReplMonitor("eval-sections", <SID>Pos(<q-args>))
command! -bar -nargs=0 LEvalLast call LitReplRun("eval-sections", "inf,inf", g:litrepl_lastcur)
command! -bar -nargs=? LInterrupt call LitReplRun("interrupt", "1.0,1.0", <SID>Pos(<q-args>))
command! -bar -nargs=0 LStatus call LitReplStatus()

let g:litrepl_loaded = 1

