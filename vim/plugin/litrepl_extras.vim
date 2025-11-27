if exists("g:litrepl_extras_loaded")
  finish
endif

if ! exists("g:litrepl_extras_script_template")
  let g:litrepl_extras_script_template = 'litrepl-*'
endif

fun! LitReplActionGlob(action)
  let l:template = LitReplGet('litrepl_extras_script_template')
  let l:pattern = substitute(l:template, '*', a:action, '')
  let l:matches = uniq(globpath(substitute($PATH,':',',','g'), l:pattern . '*', 1, 1, 1))
  if len(l:matches) == 0
    throw "No matches found for: " . l:pattern
  elseif len(l:matches) > 1
    let msg = ""
    let sep = ""
    for match in l:matches
      let msg = msg . sep . match
      if len(sep) == 0
        let sep = ", "
      endif
    endfor
    throw "Multiple matches found for: " . l:pattern . "(" . msg . ")"
  endif
  return l:matches[0]
endfun

fun! LitReplExCmdline(action, prompt, selmode, file, extras, errfile)
  call LitReplCheckVersions()
  let [action, prompt, selmode, file, extras, errfile] = [a:action, a:prompt,
        \ a:selmode, a:file, a:extras, a:errfile]

  let command = "cd \"".expand(LitReplGet('litrepl_workdir'))."\"; "
  let command = command . LitReplActionGlob(action)
  if prompt != '-'
    if len(trim(prompt)) == 0
      let prompt = input("Script input: ")
    endif
    if len(trim(prompt))>0
      let command = command . ' --prompt "'.prompt.'"'
    endif
  endif
  if len(selmode)>0 " 'raw' or 'paste'
    let command = command . ' --selection-'.selmode.' - '
  endif
  if &textwidth > 0
    let command = command . ' --textwidth '.string(&textwidth)
  endif
  if &filetype != ''
    let command = command . ' --output-format '.&filetype
  endif
  let debug = LitReplGet('litrepl_debug')
  if debug>0
    let command = command . ' --debug '
  endif
  let command = command . ' eval-code '
  if len(file)>0
    let command = command . ' ' . file
  endif
  let command = command . ' ' . extras . ' 2>>'.errfile
  return command
endfun

fun! LitReplExReplace(action, prompt, source, selmode, file, extras) range " -> int
  let [action, prompt, source] = [a:action, a:prompt, a:source]
  let errfile = LitReplGet('litrepl_errfile')
  let command = LitReplExCmdline(action, prompt, a:selmode, a:file, a:extras, errfile)
  let vimcommand = "silent! ".source."! ".command
  call LitReplLogInput(errfile, vimcommand, "<".source.">")
  call LitReplExecute(vimcommand)
  call writefile(['<end-of-stderr>'],errfile,'a')
  let errcode = v:shell_error
  call LitReplVisualize(errcode, "Failed with code (" . string(errcode) . ")")
  return errcode
endfun

fun! LitReplExReplaceFile(action, prompt, selmode, file) range " -> int
  if len(a:selmode)>0
    echom ":LPipeFile does not accept selections"
    return 1
  endif
  return LitReplExReplace(a:action, a:prompt, "%", a:selmode, a:file, "")
endfun

fun! LitReplExPushSelection(action, prompt, selmode) range
  let [action, prompt] = [a:action, a:prompt]
  let errfile = LitReplGet('litrepl_errfile')
  let command = LitReplExCmdline(action, prompt, a:selmode, "", "", errfile)
  let selection = LitReplGetVisualSelection() . "\n"
  call LitReplLogInput(errfile, command, selection)
  let result = LitReplSystem(command, selection)
  call writefile(['<end-of-stderr>'],errfile,'a')
  echo result
  let errcode = v:shell_error
  call LitReplVisualize(errcode, "Failed with code (" . string(errcode) . ")")
  return errcode
endfun

fun! LitReplExPush(action, prompt, selmode) range
  let [action, prompt] = [a:action, a:prompt]
  let errfile = LitReplGet('litrepl_errfile')
  let command = LitReplExCmdline(action, prompt, a:selmode, "", "", errfile)
  call LitReplLogInput(errfile, command, "<empty>")
  let result = LitReplSystem(command,'')
  call writefile(['<end-of-stderr>'],errfile,'a')
  echo result
  let errcode = v:shell_error
  call LitReplVisualize(errcode, "Failed with code (" . string(errcode) . ")")
  return errcode
endfun

fun! LitReplExPull(action, prompt) range
  let [action, prompt] = [a:action, a:prompt]
  let errfile = LitReplGet('litrepl_errfile')
  let command = LitReplExCmdline(action, prompt, "", "", "", errfile)
  let vimcommand = 'r!'.command .'</dev/null'
  call LitReplLogInput(errfile, vimcommand, "</dev/null>")
  call LitReplExecute(vimcommand)
  call writefile(['<end-of-stderr>'],errfile,'a')
  let errcode = v:shell_error
  call LitReplVisualize(errcode, "Failed with code (" . string(errcode) . ")")
  return errcode
endfun

fun! LitReplExReplaceSelectionOrPull(action, prompt, selmode) range " -> int
  if len(a:selmode)>0
    return LitReplExReplace(a:action, a:prompt, "'<,'>", a:selmode, "", "")
  else
    return LitReplExPull(a:action, a:prompt)
  endif
endfun

fun! LitReplExPushSelectionOrPush(action, prompt, selmode) range " -> int
  if len(a:selmode)>0
    return LitReplExPushSelection(a:action, a:prompt, a:selmode)
  else
    return LitReplExPush(a:action, a:prompt, a:selmode)
  endif
endfun

fun! Arg0(line)
  " Split the line into words and return the first word
  return split(a:line)[0]
endfun

fun! ArgStar(line)
  let first_space_index = match(a:line, '\s')
  if first_space_index != -1
    return trim(a:line[first_space_index:])
  else
    return ''
  endif
endfun

fun! ArgSelMode(range, bang)
  if a:range != 0
    if a:bang == '!'
      return "raw"
    else
      return "paste"
    endif
  else
    return ""
  endif
endfun

fun! LitReplExCompletion(ArgLead, CmdLine, CursorPos)
  if a:CmdLine =~ '\<\w\+\>\s\<\w\+\>\s'
    return []
  endif
  let result = []
  let template = LitReplGet('litrepl_extras_script_template')
  let executables = globpath(substitute($PATH,':',',','g'), template, 1, 1, 1)
  for e in executables
    let matches = matchlist(fnamemodify(e, ':t'), substitute(template, '\*', '\\(.\\+\\)', ''))
    if len(matches)>=2
      call add(result, matches[1].' ')
    endif
  endfor
  return filter(result, 'v:val =~ "^".a:ArgLead')
endfun

if exists(":LPipe") != 2
  command! -complete=customlist,LitReplExCompletion -range -bar -nargs=* -bang LPipe
        \ call LitReplExReplaceSelectionOrPull(
        \        Arg0(<q-args>), ArgStar(<q-args>), ArgSelMode(<range>, "<bang>"))
endif

if exists(":LPush") != 2
  command! -complete=customlist,LitReplExCompletion -range -bar -nargs=* -bang LPush
        \ call LitReplExPushSelectionOrPush(Arg0(<q-args>), ArgStar(<q-args>),
        \        ArgSelMode(<range>, "<bang>"))
endif

if exists(":LPipeFile") != 2
  command! -complete=customlist,LitReplExCompletion -range -bar -nargs=* -bang LPipeFile
        \ call LitReplExReplaceFile(Arg0(<q-args>), ArgStar(<q-args>),
        \        ArgSelMode(<range>, "<bang>"), expand("%:p"))
endif

let g:litrepl_extras_loaded = 1
