if exists("g:litrepl_loaded")
  finish
endif
if ! exists("g:litrepl_bin")
  " TODO: Delay the expansion until the LitReplExe or alike.
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
  " No colons `:` are allowed in this file name
  let g:litrepl_map_cursor_output = '/tmp/litrepl_cursor.txt'
endif
if ! exists("g:litrepl_python_interpreter")
  let g:litrepl_python_interpreter = 'auto'
endif
if ! exists("g:litrepl_ai_interpreter")
  let g:litrepl_ai_interpreter = 'auto'
endif
if ! exists("g:litrepl_workdir")
  let g:litrepl_workdir = '%:p:h'
endif
if ! exists("g:litrepl_python_auxdir")
  let g:litrepl_python_auxdir = ''
endif
if ! exists("g:litrepl_ai_auxdir")
  let g:litrepl_ai_auxdir = ''
endif
if ! exists("g:litrepl_timeout")
  let g:litrepl_timeout = 0.5
endif
if ! exists("g:litrepl_pending")
  let g:litrepl_pending = 33
endif
if ! exists("g:litrepl_dump_mon")
  let g:litrepl_dump_mon = 0
endif

fun! LitReplExe()
  let oldpath = getenv('PATH')
  try
    call setenv('PATH', g:litrepl_bin.':'.oldpath)
    return exepath(g:litrepl_exe)
  finally
    call setenv('PATH', oldpath)
  endtry
endfun

if ! exists("g:litrepl_version")
  let devroot = getenv('LITREPL_ROOT')
  if ! empty(devroot)
    let g:litrepl_plugin_version = substitute(system(LitReplExe().' --version'),"\n","",'g')
  else
    let g:litrepl_plugin_version = 'version-to-be-filled-by-the-packager'
  endif
endif
if ! exists("g:litrepl_check_versions")
  let g:litrepl_check_versions = 1
endif

" Return the most-used common part of litrepl command line based on the plugin
" settings
fun! LitReplCmd()
  if g:litrepl_check_versions == 1
    let g:litrepl_tool_version = substitute(system(LitReplExe().' --version'),"\n","",'g')
    if v:shell_error != 0
      echohl ErrorMsg
      echom "Error: `litrepl` system tool failed to report its version!"
            \" Visit https://github.com/sergei-mironov/litrepl#installation"
      echohl None
    else
      if g:litrepl_tool_version != g:litrepl_plugin_version
        echohl WarningMsg
        echom "Warning: lirepl tool version (" . g:litrepl_tool_version . ")"
              \" does not match the vim plugin version (" . g:litrepl_plugin_version . ")"
        echohl None
      endif
      let g:litrepl_check_versions = 0
    endif
  endif
  let cmd = LitReplExe() . ' --workdir="'.expand(g:litrepl_workdir).'"'
  if g:litrepl_python_auxdir != ''
    let cmd = cmd . ' --python-auxdir="'.g:litrepl_python_auxdir.'"'
  endif
  if g:litrepl_ai_auxdir != ''
    let cmd = cmd . ' --ai-auxdir="'.g:litrepl_ai_auxdir.'"'
  endif
  let ft = &filetype
  let cur = getcharpos('.')
  let tw = string(&textwidth)
  let cmd = cmd .
        \ ' --python-interpreter="'.g:litrepl_python_interpreter.'"'.
        \ ' --ai-interpreter="'.g:litrepl_ai_interpreter.'"'.
        \ ' --pending-exit='.g:litrepl_pending.
        \ ' --debug='.g:litrepl_debug.
        \ ' --filetype='.ft.
        \ ' --map-cursor='.cur[1].':'.cur[2].':'.g:litrepl_map_cursor_output.
        \ ' --result-textwidth='.tw.
        \ ' '
  return cmd
endfun

" Return the most-used common part of litrepl command line based on the plugin
" settings with the additional timeout argument.
fun! LitReplCmdTimeout(timeout)
  return LitReplCmd().' --timeout='.a:timeout.' '
endfun

fun! LitReplOpenErr(file, message)
  if bufwinnr(a:file) <= 0
    let nr = winnr()
    execute "botright vs ".a:file
    execute "setlocal autoread"
    execute string(nr) . 'wincmd w'
  endif
  if a:message != ''
    echohl ErrorMsg
    echon a:message
    echohl None
  endif
endfun

fun! LitReplUpdateCursor(cur)
  let cur = a:cur
  try
    let newrow = str2nr(readfile(g:litrepl_map_cursor_output)[0])
    if newrow != 0
      let cur[1] = newrow
    endif
    call setcharpos('.', cur)
  catch /E484/
  endtry
endfun

fun! LitReplNotice(message)
  echohl MoreMsg
  echon a:message
  echohl None
endfun

fun! LitReplVisualize(errcode, result)
  let [errcode, result] = [a:errcode, a:result]
  if errcode == g:litrepl_pending
    call LitReplNotice('Re-evaluate to continue')
  else
    if errcode == 0
      call LitReplNotice('Done')
      if g:litrepl_always_show_stderr != 0
        call LitReplOpenErr(g:litrepl_errfile, result)
      endif
    else
      call LitReplOpenErr(g:litrepl_errfile, result)
    endif
  endif
endfun

fun! LitReplRun(command, input) range
  " Take the command part of litrepl command-line and it's input and return
  " errorcode and stdout.
  let cur = getcharpos('.')
  let cmd = LitReplCmdTimeout('inf').' '.a:command.' 2>'.g:litrepl_errfile
  let result = system(cmd, a:input)
  let errcode = v:shell_error
  return [errcode, result]
endfun

fun! LitReplRunV(command, input) range
  let [errcode, result] = LitReplRun(a:command, a:input)
  call LitReplVisualize(errcode, result)
  return [errcode, result]
endfun

fun! LitReplRunBuffer(command, timeout) range
  " Run the current buffer 'through' the litrepl processor.
  let cur = getcharpos('.')
  let ft = &filetype
  let cmd = '%!'.LitReplCmdTimeout(a:timeout).' '.a:command.' 2>'.g:litrepl_errfile
  silent execute cmd
  let errcode = v:shell_error
  return errcode
endfun

fun! LitReplRunBufferVC(command, timeout) range
  " Run the current buffer 'through' the litrepl processor. Print the status and
  " update the cursor if needed.
  let cur = getcharpos('.')
  let errcode = LitReplRunBuffer(a:command, a:timeout)
  call LitReplVisualize(errcode, '')
  call LitReplUpdateCursor(cur)
  return errcode
endfun

fun! LitReplRunBufferOrUndo(command, timeout)
  " We use a hack to force remembering the undo position
  execute "normal! I "
  execute "normal! x"
  let cur = getcharpos('.')
  let command = '--propagate-sigint ' . a:command
  let errcode = LitReplRunBufferVC(command, a:timeout)
  if errcode == 0 || errcode == g:litrepl_pending
    return errcode
  else
    execute "u"
    call setcharpos('.', cur)
    return 0
  endif
endfun

let g:log_count = 1
function! SaveStringToFile(dump)
  let l:dir = "_dump"
  if !isdirectory(l:dir)
    call mkdir(l:dir, "p")
  endif
  let l:filename = printf("_dump/03%d.log", g:log_count)
  call writefile(a:dump, l:filename)
  let g:log_count += 1
endfunction

" Continuosly run litrepl until error or completion
" Notes: [1] - Opens a new undo block
fun! LitReplRunBufferMonitor(command)
  let cur = getcharpos('.')
  try
    let g:log_count = 0
    while 1
      let &ul=&ul " [1]
      let errcode = LitReplRunBuffer(a:command, g:litrepl_timeout.',0.0')

      if g:litrepl_dump_mon == 1
        let dump = ["CODE", string(errcode), "CONTENTS"]
        call extend(dump,getline(1, '$'))
        call SaveStringToFile(dump)
      endif

      if errcode == 0
        LitReplVisualize(errocde, '')
        break
      else
        if errcode == g:litrepl_pending
          silent execute "redraw"
        else
          execute "u"
          call setcharpos('.', cur)
          call LitReplVisualize(errcode, '')
          break
        endif
      endif
    endwhile
  catch /Vim:Interrupt/
    call setcharpos('.', cur)
  endtry
endfun

" Prints the Litrepl status informaiton
" Notes: [1] - A hack to remember the undo position
fun! LitReplStatus()
  let cur = getcharpos('.')
  execute "normal! I "
  execute "normal! x"
  " ^^^ [1]
  silent execute '%!'.LitReplCmd(). ' --verbose status 2>'.g:litrepl_errfile.' >&2'
  call setcharpos('.', cur)
  execute "u"
  call LitReplOpenErr(g:litrepl_errfile, '')
endfun

let b:litrepl_lastpos = "0:0"

fun! LitReplPos(arg)
  let p = getcharpos('.')
  let loc = p[1].":".p[2]
  if a:arg == ""
    let pos = loc
  elseif tolower(a:arg) == "all"
    let pos = "0..$"
  elseif tolower(a:arg) == "above"
    let pos = "0..".loc
  elseif tolower(a:arg) == "below"
    let pos = loc."..$"
  else
    let pos = a:arg
  endif
  let b:litrepl_lastpos = pos
  return pos
endfun

fun! LitReplVersion()
  echomsg systemlist(LitReplCmd()." --version")[0]
endfun

fun! LitReplTerm(what)
  execute "terminal ".LitReplCmd()." repl ".a:what
endfun

if !exists(":LStart")
  command! -bar -nargs=? LStart call LitReplRunV('start '.<q-args>, '')
endif
if !exists(":LStop")
  command! -bar -nargs=? LStop call LitReplRunV('stop '.<q-args>, '')
endif
if !exists(":LRestart")
  command! -bar -nargs=? LRestart call LitReplRunV('restart '.<q-args>, '')
endif
if !exists(":LPP")
  command! -bar -nargs=0 LPP call LitRepRunV('parse-print', '')
endif
if !exists(":LRepl")
  command! -bar -nargs=? LRepl call LitReplTerm(<q-args>)
endif
if !exists(":LTerm")
  command! -bar -nargs=? LTerm call LitReplTerm(<q-args>)
endif
if !exists(":LOpenErr")
  command! -bar -nargs=0 LOpenErr call LitReplOpenErr(g:litrepl_errfile,'')
endif
if !exists(":LVersion")
  command! -bar -nargs=0 LVersion call LitReplVersion()
endif
if !exists(":LEval")
  command! -bar -nargs=? LEval call LitReplRunBufferOrUndo("eval-sections ".LitReplPos(<q-args>), "inf,inf")
endif
if !exists(":LEvalAsync")
  command! -bar -nargs=? LEvalAsync call LitReplRunBufferOrUndo("eval-sections ".LitReplPos(<q-args>), g:litrepl_timeout.',0.0')
endif
if !exists(":LEvalMon")
  command! -bar -nargs=? LEvalMon call LitReplRunBufferMonitor("eval-sections ".LitReplPos(<q-args>))
endif
if !exists(":LEvalLast")
  command! -bar -nargs=0 LEvalLast call LitReplRunBufferOrUndo("eval-sections ".b:litrepl_lastpos, "inf,inf")
endif
if !exists(":LInterrupt")
  command! -bar -nargs=? LInterrupt call LitReplRunBufferOrUndo("interrupt ".LitReplPos(<q-args>), "1.0,1.0")
endif
if !exists(":LStatus")
  command! -bar -nargs=0 LStatus call LitReplStatus()
endif

let g:litrepl_loaded = 1

