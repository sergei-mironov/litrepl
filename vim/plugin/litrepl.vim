if exists("g:litrepl_loaded")
  finish
endif

fun! LitReplGetTempDir()
  " Get the system temporary files directory from $TMPDIR, $TEMP, or $TMP
  if exists('$TMPDIR')
    return $TMPDIR
  elseif exists('$TEMP')
    return $TEMP
  elseif exists('$TMP')
    return $TMP
  else
    return '/tmp'
  endif
endfun

if ! exists("g:litrepl_always_show_stderr")
  let g:litrepl_always_show_stderr = 0
endif
if ! exists("g:litrepl_debug")
  let g:litrepl_debug = 0
endif
if ! exists("g:litrepl_errfile")
  let g:litrepl_errfile = LitReplGetTempDir() . '/litrepl.err'
endif
if ! exists("g:litrepl_map_cursor_output")
  " No colons `:` are allowed in this file name
  let g:litrepl_map_cursor_output = LitReplGetTempDir() . '/litrepl_cursor.txt'
endif
if ! exists("g:litrepl_python_interpreter")
  let g:litrepl_python_interpreter = 'auto'
endif
if ! exists("g:litrepl_ai_interpreter")
  let g:litrepl_ai_interpreter = 'auto'
endif
if ! exists("g:litrepl_workdir")
  if exists('$LITREPL_WORKDIR')
    let g:litrepl_workdir = ''
  else
    let g:litrepl_workdir = '%:p:h'
  endif
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
if ! exists("g:litrepl_shellexec_prefix")
  let g:litrepl_shellexec_prefix = "if test -f $HOME/.bashrc; then . $HOME/.bashrc; fi"
endif

fun! LitReplGet(name)
  if exists('b:'.a:name)
    return get(b:, a:name, '')
  elseif exists('g:'.a:name)
    return get(g:, a:name, '')
  else
    return ''
  endif
endfun

fun! LitReplExe()
  if exists('$LITREPL')
    let litrepl = $LITREPL
  else
    let litrepl = exepath('litrepl')
  endif
  return litrepl
endfun

fun! LitReplSystemL(line, input)
  let ret = ''
  let line = a:line
  try
    let $LITREPL_FILE = expand('%:p')
    let line = LitReplGet('litrepl_shellexec_prefix').';'.line
    silent let ret = systemlist(line, a:input)
  finally
    unlet $LITREPL_FILE
  endtry
  return ret
endfun

fun! LitReplSystem(line, input)
  return join(LitReplSystemL(a:line, a:input),'\n')
endfun

fun! LitReplExecute(prefix, line)
  let [prefix,line] = [a:prefix, a:line]
  try
    let $LITREPL_FILE = expand('%:p')
    let line = LitReplGet('litrepl_shellexec_prefix').';'.line
    execute prefix . line
  finally
    unlet $LITREPL_FILE
  endtry
endfun

fun! LitReplTerminal(line)
  call LitReplExecute('terminal ++shell ', a:line)
endfun

if ! exists("g:litrepl_plugin_version")
  let devroot = getenv('LITREPL_ROOT')
  if ! empty(devroot)
    let g:litrepl_plugin_version = substitute(
      \ LitReplSystem(LitReplExe().' --version',''),"\n",
      \ "",'g')
  else
    let g:litrepl_plugin_version = 'version-to-be-filled-by-the-packager'
  endif
endif
if ! exists("g:litrepl_check_versions")
  let g:litrepl_check_versions = 1
endif

fun! LitReplCheckVersions()
  if LitReplGet('litrepl_check_versions') == 1
    let g:litrepl_tool_version = substitute(LitReplSystem(LitReplExe().' --version', ''),"\n","",'g')
    if v:shell_error != 0
      echohl ErrorMsg
      echom "Error: `litrepl` system tool failed to report its version!"
            \" Visit https://github.com/sergei-mironov/litrepl#installation"
      echohl None
    else
      if LitReplGet('litrepl_tool_version') != LitReplGet('litrepl_plugin_version')
        echohl WarningMsg
        echom "Warning: lirepl tool version (" . LitReplGet('litrepl_tool_version') .")"
              \" does not match the vim plugin version (" .  LitReplGet('litrepl_plugin_version') . ")"
        echohl None
      endif
      let g:litrepl_check_versions = 0
    endif
  endif
endfun

fun! LitReplCmd()
  call LitReplCheckVersions()
  let cmd = LitReplExe()
  if LitReplGet('litrepl_workdir') != ''
    " let cmd  = cmd . ' --workdir="'.expand(LitReplGet('litrepl_workdir')).'"'
    let cmd  = "cd \"".expand(LitReplGet('litrepl_workdir'))."\"; ".cmd
  endif
  if LitReplGet('litrepl_python_auxdir') != ''
    let cmd = cmd . ' --python-auxdir="'.expand(LitReplGet('litrepl_python_auxdir')).'"'
  endif
  if LitReplGet('litrepl_ai_auxdir') != ''
    let cmd = cmd . ' --ai-auxdir="'.expand(LitReplGet('litrepl_ai_auxdir')).'"'
  endif
  if LitReplGet('litrepl_python_interpreter') != ''
    let cmd = cmd .' --python-interpreter="'.LitReplGet('litrepl_python_interpreter').'"'
  endif
  if LitReplGet('litrepl_ai_interpreter') != ''
    let cmd = cmd . ' --ai-interpreter="'.LitReplGet('litrepl_ai_interpreter').'"'
  endif
  let ft = &filetype
  if ft == ''
    let ft = "auto"
  endif
  let cur = getcharpos('.')
  let tw = string(&textwidth)
  let cmd = cmd .
        \ ' --pending-exitcode='.LitReplGet('litrepl_pending').
        \ ' --debug='.LitReplGet('litrepl_debug').
        \ ' --filetype='.ft.
        \ ' --map-cursor='.cur[1].':'.cur[2].':'.LitReplGet('litrepl_map_cursor_output').
        \ ' --result-textwidth='.tw.
        \ ' '
  return cmd
endfun

fun! LitReplCmdTimeout(timeout)
  return LitReplCmd().' --timeout='.a:timeout.' '
endfun

fun! LitReplOpenErrS(message, splitcmd)
  " Open error file and show the message
  let file = LitReplGet('litrepl_errfile')
  if bufwinnr(file) <= 0
    let nr = winnr()
    execute "botright ".a:splitcmd." ".file
    execute "setlocal autoread"
    execute string(nr) . 'wincmd w'
  endif
  if a:message != ''
    echohl ErrorMsg
    echon a:message
    echohl None
  endif
endfun

fun! LitReplOpenErr(message)
  " Open error file and show the message
  return LitReplOpenErrS(a:message, "vs")
endfun

fun! LitReplUpdateCursor(view)
  let [view] = [a:view]
  try
    let newrow = str2nr(readfile(LitReplGet('litrepl_map_cursor_output'))[0])
    if newrow != 0
      let view['lnum'] = newrow
      let b:litrepl_lastpos = view['lnum'].":".view['col']
    endif
    call winrestview(view)
  catch /E484/
  endtry
endfun

fun! LitReplNotice(message)
  echohl MoreMsg
  echon a:message
  echohl None
endfun

fun! LitReplVisualize(errcode)
  let [errcode] = [a:errcode]
  if errcode == LitReplGet('litrepl_pending')
    call LitReplNotice('Re-evaluate to continue')
  else
    if errcode == 0
      call LitReplNotice('Done')
      if LitReplGet('litrepl_always_show_stderr') != 0
        call LitReplOpenErr('')
      endif
    else
      call LitReplOpenErr("Failed with code (".string(errcode).")")
    endif
  endif
endfun

fun! LitReplLogInput(file, command, input) range
  let l:dir = fnamemodify(a:file, ':h')
  if !isdirectory(l:dir)
    call mkdir(l:dir, 'p')
  endif
  let l:file = a:file
  call writefile([
    \ "REPORT", "======", "",
    \ "litrepl:     ".LitReplGet('litrepl_tool_version'),
    \ "litrepl.vim: ".LitReplGet('litrepl_plugin_version'), "",
    \ "COMMAND", "-------",
    \ a:command, "",
    \ "STDIN", "------"] +
    \ split(a:input, "\n") + ["",
    \ "STDERR", "------",
    \ ], l:file, '')
endfun

fun! LitReplRun(command, input) range
  " Take the command part of litrepl command-line and its input and return
  " errorcode and stdout.
  let cur = getcharpos('.')
  let errfile = LitReplGet('litrepl_errfile')
  let cmd = LitReplCmdTimeout('inf').' '.a:command.' 2>>'.errfile
  call LitReplLogInput(errfile, cmd, a:input)
  let result = LitReplSystemL(cmd, a:input)
  call writefile(['<end-of-stderr>'],errfile,'a')
  let errcode = v:shell_error
  return [errcode, result]
endfun

fun! LitReplRunV(command, input) range
  let [errcode, result] = LitReplRun(a:command, a:input)
  call LitReplVisualize(errcode)
  return [errcode, result]
endfun

fun! LitReplRunBuffer(command, timeout) range
  " Run the current buffer 'through' the litrepl processor.
  " [1] - Here we execute a fake command to aid vim undo-redo buffer
  "       ref. https://vim.fandom.com/wiki/Restore_the_cursor_position_after_undoing_text_change_made_by_a_script
  let errfile = LitReplGet('litrepl_errfile')
  let cmd = LitReplCmdTimeout(a:timeout).' '.a:command.' 2>>'.errfile
  call LitReplLogInput(errfile, cmd, "<vim-buffer>")
  let input = join(getline(1, '$'), "\n")
  let input_lastline = getline('$')
  let result = LitReplSystemL(cmd, input)
  call writefile(['<end-of-stderr>'],errfile,'a')
  let errcode = v:shell_error
  if errcode == 0 || errcode == LitReplGet('litrepl_pending')
    " [1]
    execute "normal! I "
    execute "normal! x"
    silent %delete _
    call append(0, result)
    if input_lastline != '' && getline('$') == ''
      silent execute '%delete '.string(getpos('$')[1])
    endif
  endif
  return errcode
endfun

fun! LitReplRunBufferVC(command, timeout) range
  " Run the current buffer 'through' the litrepl processor. Print the status and
  " update the cursor if needed.
  let view = winsaveview()
  let errcode = LitReplRunBuffer(a:command, a:timeout)
  call LitReplVisualize(errcode)
  call LitReplUpdateCursor(view)
  return errcode
endfun

fun! LitReplRunBufferOrUndo(command, timeout)
  " We use a hack to force remembering the undo position
  " execute "normal! I "
  " execute "normal! x"
  " let cur = getcharpos('.')
  let command = '--detach-on-sigint ' . a:command
  let errcode = LitReplRunBufferVC(command, a:timeout)
  " if errcode == 0 || errcode == LitReplGet('litrepl_pending')
  return errcode
  " else
    " execute "u"
    " call setcharpos('.', cur)
    " return 0
  " endif
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

fun! LitReplRunBufferMonitor()
  let view = winsaveview()
  try
    let g:log_count = 0
    while 1
      " let &ul=&ul " [1]
      let view = winsaveview()
      let command = "eval-sections ".view['lnum'].":".(view['col']+1)
      let errcode = LitReplRunBuffer(command, LitReplGet('litrepl_timeout').',0.0')

      if LitReplGet('litrepl_dump_mon') == 1
        let dump = ["CODE", string(errcode), "CONTENTS"]
        call extend(dump,getline(1, '$'))
        call SaveStringToFile(dump)
      endif

      if errcode == 0
        call LitReplUpdateCursor(view)
        break
      else
        if errcode == LitReplGet('litrepl_pending')
          call LitReplUpdateCursor(view)
          silent execute "redraw"
        else
          call winrestview(view)
          break
        endif
      endif
    endwhile
  catch /Vim:Interrupt/
    call winrestview(view)
  endtry
endfun

fun! LitReplStatus()
  if LitReplGet('litrepl_debug') != 0
    let [flag,splitcmd] = ["--verbose","vs"]
  else
    let [flag,splitcmd] = ["","3split"]
  endif
  let cur = getcharpos('.')
  execute "normal! I "
  execute "normal! x"
  let cmd = LitReplCmd().' '.flag.' status 2>'.LitReplGet('litrepl_errfile').' >&2'
  call LitReplExecute("%!", cmd)
  call setcharpos('.', cur)
  execute "u"
  call LitReplOpenErrS('',splitcmd)
endfun

let b:litrepl_lastpos = "0:0"

fun! LitReplPos(arg)
  let cursor = getcharpos('.')
  let loc = cursor[1].":".cursor[2]
  let pos = a:arg
  let pos = substitute(pos,'all','1..$','g')
  let pos = substitute(pos,'above','1..@','g')
  let pos = substitute(pos,'below','@..$','g')
  let pos = substitute(pos,'@',loc,'g')
  if pos == ""
    let pos = loc
  endif
  let b:litrepl_lastpos = pos
  return pos
endfun

fun! LitReplVersion()
  echomsg systemlist(LitReplCmd()." --version")[0]
endfun

fun! LitReplTerm(what)
  let errfile = LitReplGet('litrepl_errfile')
  let cmd = LitReplCmd()." repl ".a:what
  call LitReplLogInput(errfile, cmd, "<none>")
  call writefile(['(stderr is not captured)'],errfile,'a')
  call LitReplTerminal(cmd)
endfun

fun! LitReplGetVisualSelection() range
  " Get visual selection
  let [line_start, column_start] = getpos("'<")[1:2]
  let [line_end, column_end] = getpos("'>")[1:2]
  let lines = getline(line_start, line_end)
  if len(lines) == 0
    return ""
  endif
  let lines[-1] = lines[-1][: column_end - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][column_start - 1:]
  return join(lines, "\n")
endfun

fun! LitReplEvalSelection(type) range " -> [int, string]
  " Evaluate the selection and pastes the result next after it.
  let selection = LitReplGetVisualSelection()
  let [line_end, column_end] = getpos("'>")[1:2]
  let [errcode, result] = LitReplRunV('eval-code '.a:type, selection)
  if errcode == 0
    call append(line_end, result)
  else
    call LitReplOpenErr("Failed (".string(errcode).")")
  endif
  return [errcode, result]
endfun

fun! LitReplTypeCompletion(ArgLead, CmdLine, CursorPos)
  let l:completions = ['python', 'ai', 'sh']
  let l:matches = []
  for e in l:completions
    if e =~ '^' . a:ArgLead
      call add(l:matches, e)
    endif
  endfor
  return l:matches
endfun

if !exists(":LStart")
  command! -bar -nargs=1 -complete=customlist,LitReplTypeCompletion LStart call LitReplRunV('start '.<q-args>, '')
endif
if !exists(":LStop")
  command! -bar -nargs=? -complete=customlist,LitReplTypeCompletion LStop call LitReplRunV('stop '.<q-args>, '')
endif
if !exists(":LRestart")
  command! -bar -nargs=? -complete=customlist,LitReplTypeCompletion LRestart call LitReplRunV('restart '.<q-args>, '')
endif
if !exists(":LPP")
  command! -bar -nargs=0 LPP call LitRepRunV('parse-print', '')
endif
if !exists(":LRepl")
  command! -bar -nargs=1 -complete=customlist,LitReplTypeCompletion LRepl call LitReplTerm(<q-args>)
endif
if !exists(":LTerm")
  command! -bar -nargs=1 -complete=customlist,LitReplTypeCompletion LTerm call LitReplTerm(<q-args>)
endif
if !exists(":LOpenErr")
  command! -bar -nargs=0 LOpenErr call LitReplOpenErr('')
endif
if !exists(":LVersion")
  command! -bar -nargs=0 LVersion call LitReplVersion()
endif
if !exists(":LEval")
  command! -bar -nargs=? LEval call LitReplRunBufferOrUndo("eval-sections ".LitReplPos(<q-args>), "inf,inf")
endif
if !exists(":LEvalAsync")
  command! -bar -nargs=? LEvalAsync call LitReplRunBufferOrUndo("eval-sections ".LitReplPos(<q-args>), LitReplGet('litrepl_timeout').',0.0')
endif
if !exists(":LEvalMon")
  command! -bar -nargs=0 LEvalMon call LitReplRunBufferMonitor()
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

