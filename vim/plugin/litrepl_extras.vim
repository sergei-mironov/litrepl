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

fun! LitReplRegionRead(region) range " -> string
  let [line_start, column_start, line_end, column_end] = a:region
  let lines = getline(line_start, line_end)
  if len(lines) == 0
    return ""
  endif
  let lines[-1] = lines[-1][: column_end - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][column_start - 1:]
  return join(lines, "\n")
endfun

fun! LitReplRegionFromSelection() range " -> [int, int, int, int]
  let [line_start, column_start] = getpos("'<")[1:2]
  let [line_end, column_end] = getpos("'>")[1:2]
  return [line_start, column_start, line_end, column_end]
endfun

fun! LitReplRegionFromCursor() range " -> [int, int, int, int]
  let [line, column] = getpos(".")[1:2]
  return [line, column, line, column-1]
endfun

fun! LitReplRegionFromFile() range " -> [int, int, int, int]
  let [line, column] = getpos("$")[1:2]
  return [1, 0, line, len(getline(line))]
endfun

fun! LitReplRegionToSelection(region) range
  let [line_start, column_start, line_end, column_end] = a:region
  call setpos("'<", [0, line_start, column_start, 0])
  call setpos("'>", [0, line_end, column_end, 0])
  execute "normal gv"
endfun

fun! LitReplRegionReplace(region, replacement) range " -> [int, int, int, int]
  " Replace the specified region with the `replacement` string, adjust the
  " selection registers accordingly. Return the new region.
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

fun! LitReplEvalSelection(type) range " -> [int, string]
  " Evaluate the selection and pastes the result next after it.
  let selection = LitReplGetVisualSelection()
  let [line_end, column_end] = getpos("'>")[1:2]
  let [errcode, result] = LitReplRunV('eval-code '.a:type, selection)
  if errcode == 0
    let result = split(result, '\n')
    call append(line_end, result)
  else
    call LitReplOpenErr("Failed (".string(errcode).")")
  endif
  return [errcode, result]
endfun

fun! LitReplAIQuery(selection, file, prompt) range " -> [int, string]
  " Create an AI prompt using the following method: (1) start with the
  " user-provided prompt string, (2) incorporate user input, (3) if the prompt
  " is still vacant or contains `/S`, include the `selection`, (4) append
  " the file contents if `/F` is present in the text and `file` is not zero.
  "
  " The completed prompt is submitted to the AI interpreter.
  "
  " The function outputs the exit code from `litrepl eval-code ai` alongside the
  " interpreter's response.

  let [selection, prompt, file, header] = [a:selection, a:prompt, a:file, ""]

  if len(trim(prompt)) == 0
    let hint = "Hint: "
    if len(selection)>0
      let hint = hint . "type /S to insert the selection, "
    endif
    if file > 0
      let hint = hint . "type /F to insert current file"
    endif
    let prompt = input(hint . "\nYour question: ")
    if len(trim(prompt)) == 0 && len(selection)>0
      let prompt = "/S"
    endif
  endif

  if len(selection)>0
    let header = header.
      \ "/clear buffer:in\n".
      \ "/paste on\n".
      \ selection."\n".
      \ "/paste off\n".
      \ "/cp buffer:in buffer:sel\n"
    let prompt = substitute(prompt, "/S", "\n/append buffer:\"sel\" buffer:\"in\"\n", "g")
  endif

  if file > 0
    let header = header.
      \ "/clear buffer:in\n".
      \ "/cp file:\"".expand('%:p')."\" buffer:file\n"
    let prompt = substitute(prompt, "/F", "\n/append buffer:\"file\" buffer:\"in\"\n", "g")
  endif

  " echomsg "|P " . header. prompt . " P|"
  return LitReplRun('eval-code ai', header . prompt)
endfun

let b:airegion = LitReplRegionFromCursor()

fun! LitReplTaskNew(scope, prompt) range " -> [int, string]
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
      " Show response in the terminal
      execute "terminal ".LitReplCmd()." repl ai"
      call feedkeys("/cat out\n")
    else
      let b:airegion = LitReplRegionReplace(b:airegion, trim(result))
    endif
  else
    call LitReplOpenErr("Failed (".string(errcode).")")
  endif
  return [errcode, result]
endfun

if !exists(":LAI")
  command! -range -bar -nargs=* LAI call LitReplTaskNew(<range>!=0, <q-args>)
endif
if !exists(":LAITell")
  command! -range -bar -nargs=* LAITell call LitReplTaskNew(3, <q-args>)
endif


fun! LitReplTaskContinue(scope, prompt) range " -> [int, string]
  " Continue an AI task, by (a) taking a taget scope (0 - cursor, 1 - selection,
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


fun! LitReplStyle(scope, task) range " -> [int, string]
  " This function initiates an AI task for rephrasing text, taking a scope and a
  " prompt.  If the prompt is empty, it prompts the user to provide input with
  " hints for using the selection or file.  Calls LitReplTaskNew, instructing
  " the AI to rephrase text to sound more idiomatic, inserting the selection if
  " applicable.  Additional instructions are provided for returning unformatted
  " text and append comments. The current filetype is noted.
  let [scope, task] = [a:scope, a:task]

  let prompt = "" .
    \ "Consider the following text: " .
    \ "\n---\n/S\n---\n"

  if len(trim(task)) == 0
    let task = input("Specify the task: ")
  endif
  if len(trim(task)) == 0
    let task = "Your task is to rephrase the text so it appears more idiomatic. "
  endif
  let prompt = prompt . task . "\n" .
    \ "Please generate your main response without using any formatting. "

  let vm = visualmode()
  if scope==1 && vm == 'V'
    let prompt = prompt .
      \ "After that you can put your own comments wrapped into the appropriate comment blocks. ".
      \ "For commenting, mind that the overall text is ".&filetype." "
  endif
  let result = LitReplTaskNew(scope, prompt)
  return result
endfun
if !exists(":LAIStyle")
  command! -range -bar -nargs=* LAIStyle call LitReplStyle(<range>!=0, <q-args>)
endif

fun! LitReplAIFile(prompt) range " -> [int, string]
  " Start a new AI task focused on changing the contents of a file by (a)
  " accepting a prompt, checking if it's empty and requesting input if so, (b)
  " setting the scope to the whole file (scope=2) and constructing a task
  " description, (c) instructing to include the file content using specified
  " placeholders, (d) ensuring the output is plain without markdown formatting,
  " and (e) putting comments in the header of the resulting code.
  let prompt = a:prompt
  if len(trim(prompt)) == 0
    let prompt = input(
      \"Hint: type /S to insert the selection, ".
      \"type /F to insert current file, ".
      \"empty input implies /S\n".
      \"Your comments on the file: ")
  endif
  let tw_old = &textwidth
  let &textwidth = 0
  let result = LitReplTaskNew(2,
    \ "Your task is to change the contents of a file:" .
    \ "\n---\n/F\n---\n" .
    \ "You need to do the following: " .
    \ prompt . "\n".
    \ "Please arrange the output so the resulting program appears as-is " .
    \ "without any text formatting, especially without markdown \"```\" formatting! ".
    \ "Put your own comments in the header code comment of the resulting program.")
  let &textwidth = tw_old
  return result
endfun
if !exists(":LAIFile")
  command! -range -bar -nargs=* LAIFile call LitReplAIFile(<q-args>)
endif

fun! LitReplAICode(scope, prompt) range " -> [int, string]
  " Start a new AI task, by (a) taking a target scope, verifying if prompt is
  " empty and requesting if so, (b) if the scope is for selection, prepend an
  " example instruction, (c) combining the prompt with instructional text to
  " avoid markdown and include comment wrapping, (d) call LitReplTaskNew with
  " the constructed task description.
  let [scope, prompt] = [a:scope, a:prompt]
  if len(trim(prompt)) == 0
    let prompt = input(
      \"Hint: type /S to insert the selection, ".
      \"type /F to insert current file, ".
      \"empty input implies /S\n".
      \"Your comments on the task: ")
  endif
  if scope == 1
    let task = "Your task is to change the following code snippet: \n---\n/S\n---\n"
  else
    let task = ""
  endif
  let footer = ''.
    \ "Please print the resulting code snippet as-is " .
    \ "without any markdown formatting, especially avoid the \"```\" ".
    \ "formatting! Please preserve the original identation whenever possible! "
  let vm = visualmode()
  if (scope == 1 && vm == 'V') || (scope == 0 && getpos('.')[2] == 1)
    let footer = footer .
      \ "Wrap your own comments, if any, into the appropriate comment blocks or " .
      \ "line-comments suitable for the main programming language of the sinppet " .
      \ "e.g. by using hash-comment or \\/\\/ symbols. "
  else
    let footer = footer .
      \ "Please generate no comments, just output the code snippet! "
  endif
  if &textwidth > 0
    let footer = footer . "Please avoid generating lines longer than ".
      \ string(&textwidth)." characters. "
  endif
  return LitReplTaskNew(scope,
    \ task .
    \ "You need to do the following: " .
    \ prompt . "\n".
    \ footer)
endfun

if !exists(":LAICode")
  command! -range -bar -nargs=* LAICode call LitReplAICode(<range>!=0, <q-args>)
endif

let g:litrepl_extras_loaded = 1
