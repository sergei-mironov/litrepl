if exists("g:litrepl_extras_loaded")
  finish
endif

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

fun! LitReplRegionRead(region) range
  " Get visual selection
  let [line_start, column_start, line_end, column_end] = a:region
  let lines = getline(line_start, line_end)
  if len(lines) == 0
    return ""
  endif
  let lines[-1] = lines[-1][: column_end - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][column_start - 1:]
  return join(lines, "\n")
endfun

fun! LitReplRegionFromSelection() range
  let [line_start, column_start] = getpos("'<")[1:2]
  let [line_end, column_end] = getpos("'>")[1:2]
  return [line_start, column_start, line_end, column_end]
endfun

fun! LitReplRegionToSelection(region) range
  let [line_start, column_start, line_end, column_end] = a:region
  call setpos("'<", [0, line_start, column_start, 0])
  call setpos("'>", [0, line_end, column_end, 0])
  execute "normal gv"
endfun

fun! LitReplRegionFromCursor() range
  let [line, column] = getpos(".")[1:2]
  return [line, column, line, column]
endfun

fun! LitReplRegionFromFile() range
  let [line, column] = getpos("$")[1:2]
  return [1, 0, line, len(getline(line_end2))]
endfun

fun! LitReplRegionReplace(region, replacement) range
  " Replaces the current selection with a `replacement`, and adjusts the
  " selection registers accordingly. Returns the `replacement without change.
  let [line_start, column_start, line_end, column_end] = a:region
  let l:start_line = getline(line_start)
  let l:end_line = getline(line_end)
  let l:before_selection = strpart(l:start_line, 0, column_start-1)
  let l:after_selection = strpart(l:end_line, column_end)
  let l:last_lines = split(l:before_selection . a:replacement, "\n")
  if len(l:last_lines) > 0
    let l:column_end2 = len(l:last_lines[-1])
  else
    let l:column_end2 = 0
  endif
  let l:replacement_lines = split(l:before_selection . a:replacement . l:after_selection, "\n")
  call deletebufline(bufnr(), line_start, line_end)
  call append(line_start-1, l:replacement_lines)
  let line_end2 = max([line_start, line_start+len(l:replacement_lines)-1])
  if l:column_end2 == 0 && line_end2 > line_start
    let line_end2 = line_end2 - 1
    let column_end2 = len(getline(line_end2))
  endif
  call cursor(line_end2, column_end2)
  call setpos("'<", [0, line_start, column_start, 0])
  call setpos("'>", [0, line_end2, column_end2, 0])
  return [line_start, column_start, line_end2, column_end2]
endfun

fun! LitReplEvalSelection(type) range
  " Evaluates selection and pastes the result next after it.
  let selection = LitReplGetVisualSelection()
  let [line_end, column_end] = getpos("'>")[1:2]
  let [errcode, result] = LitReplRunV('eval-code '.a:type, selection)
  if errcode == 0
    let result = split(result, '\n')
    call append(line_end, result)
  endif
  return [errcode, result]
endfun

fun! LitReplAIQuery(selection, file, prompt) range
  " Construct an AI prompt out of the (1) user-provided prompt string (2)
  " user-provided input (3) visual selection if the prompt is empty up to now or
  " if `/S` is found in the text (4) the contents of the current file, if `/F`
  " is found in the text and `file` is non-zero.
  "
  " The prompt is then pased to the AI interpreter.
  "
  " The function returns the exit code of the `litrepl eval-code ai` along with
  " the interpreter response.
  let [selection, prompt, file] = [a:selection, a:prompt, a:file]

  if len(trim(prompt)) == 0
    let hint = "Hint: "
    if len(selection)>0
      let hint = hint . "type /S to insert the selection, "
    endif
    if file > 0
      let hint = hint .
        \"type /F to insert current file".
    endif
    let prompt = input(hint . "\nYour question: ")
    if len(trim(prompt)) == 0 && len(selection)>0
      let prompt = "/S"
    endif
  endif

  if len(selection)>0
    let prompt = "".
      \ "/clear buffer:in\n".
      \ "/paste on\n".
      \ selection."\n".
      \ "/paste off\n".
      \ "/cp buffer:in buffer:sel\n".
      \ substitute(prompt, "/S", "/append buffer:sel buffer:in\n", "g")
  endif

  if file > 0
    let prompt = "".
      \ "/clear buffer:in\n".
      \ "/cp file:\"".expand('%:p')."\" buffer:file\n" .
      \ substitute(prompt, "/F", "/append buffer:file buffer:in\n", "g")
  endif

  return LitReplRun('eval-code ai', prompt)
endfun

let b:airegion = LitReplRegionFromCursor()

fun! LitReplTaskNew(scope, prompt) range
  " Start a new AI task, by (a) taking a taget scope (0 - cursor, 1 - selection,
  " 2 - whole file, 3 - stanalone terminal) (b) combining the pompt (c)
  " piping the prompt through the interpreter and (d) populating the result.
  let [scope, prompt] = [a:scope, a:prompt]
  if scope == 0
    let b:airegion = LitReplRegionFromCursor()
    let selection = ""
  elseif scope == 1 || scope == 3
    let b:airegion = LitReplRegionFromSelection()
    let selection = LitReplRegionRead(b:airegion)
  elseif scope == 2
    let b:airegion = LitReplRegionFromFile()
    let selection = LitReplRegionRead(LitReplRegionFromSelection())
  else
    throw "Invalid scope " . string(scope)
  endif
  let [errcode, result] = LitReplAIQuery(selection, 1, prompt)
  if errcode == 0
    if scope == 3
      execute "terminal ".LitReplCmd()." repl ai"
      call feedkeys("/cat out\n")
    else
      let b:airegion = LitReplRegionReplace(b:airegion, trim(result))
    endif
  endif
  return [errcode, result]
endfun

if !exists(":LAI")
  command! -range -bar -nargs=* LAI call LitReplTaskNew(<range>!=0, <q-args>)
endif
if !exists(":LAITell")
  command! -range -bar -nargs=* LAITell call LitReplTaskNew(3, <q-args>)
endif


fun! LitReplTaskContinue(scope, prompt) range
  " Start a new AI task, by (a) taking a taget scope (0 - cursor, 1 - selection,
  " 2 - whole file, 3 - stanalone terminal) (b) combining the pompt (c)
  " piping the prompt through the interpreter and (d) populating the result.
  let [scope, prompt] = [a:scope, a:prompt]
  if scope == 0
    let selection = ""
  else
    let selection = LitReplRegionRead(LitReplRegionFromSelection())
  endif
  let [errcode, result] = LitReplAIQuery(selection, 1, prompt)
  if errcode == 0
    let b:airegion = LitReplRegionReplace(b:airegion, trim(result))
  endif
  return [errcode, result]
endfun

if !exists(":LAICont")
  command! -range -bar -nargs=* LAICont call LitReplTaskContinue(<range>!=0, <q-args>)
endif


fun! LitReplStyle(scope, prompt) range
  let prompt = a:prompt
  if len(trim(prompt)) == 0
    let prompt = input(
      \"Hint: type /S to insert the selection, ".
      \"type /append buffer:file buffer:in to insert current file, ".
      \"empty input implies /S\n".
      \"Your comments on style: ")
  endif
  return LitReplTaskNew(a:scope,
    \ "Your task is to rephrase the following text so it appears " .
    \ "as more idiomatic phrase: " .
    \ "\n---\n/S\n---\n" .
    \ prompt . "\n" .
    \ "Please provide the rephrased text without formatting and after that " .
    \ "your comments using the appropriate comment blocks. ".
    \ "The current file type is ".&filetype)
endfun
command! -range -bar -nargs=* LAIStyle call LitReplStyle(<range>!=0, <q-args>)

fun! LitReplAIFile(prompt) range
  let prompt = a:prompt
  if len(trim(prompt)) == 0
    let prompt = input(
      \"Hint: type /S to insert the selection, ".
      \"type /F to insert current file, ".
      \"empty input implies /S\n".
      \"Your comments on style: ")
  endif
  return LitReplTaskNew(2,
    \ "Your task is to change the contents of a file:" .
    \ "\n---\n/F\n---\n" .
    \ "You need to do the following: " .
    \ prompt . "\n".
    \ "Please arrange the output so the resulting program appears as-is " .
    \ "without any text formatting, especially without markdown \"```\" formatting! ".
    \ "Put your own comments in the header code comment of the resulting program.")
endfun
command! -range -bar -nargs=* LAIFile call LitReplAIFile(<q-args>)

fun! LitReplAICode(scope, prompt) range
  let prompt = a:prompt
  if len(trim(prompt)) == 0
    let prompt = input(
      \"Hint: type /S to insert the selection, ".
      \"type /F to insert current file, ".
      \"empty input implies /S\n".
      \"Your comments on style: ")
  endif
  if a:scope == 1
    let example = "Your task is to change the following code snippet: \n---\n/S\n---\n"
  else
    let example = ""
  endif
  return LitReplTaskNew(a:scope,
    \ example .
    \ "You need to do the following: " .
    \ prompt . "\n".
    \ "Please print the resulting program as-is " .
    \ "without any text formatting, especially avoid markdown \"```\" ".
    \ "formatting! Wrap your own comments, if any, into the code comments ".
    \ "e.g. by using hash-comment or \\/\\/ symbols.")
endfun

command! -range -bar -nargs=* LAICode call LitReplAICode(<range>!=0, <q-args>)

let g:litrepl_extras_loaded = 1
