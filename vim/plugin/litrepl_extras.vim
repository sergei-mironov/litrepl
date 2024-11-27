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

" fun! LitReplRegionFromSelection() range
"   let [line_start, column_start] = getpos("'<")[1:2]
"   let [line_end, column_end] = getpos("'>")[1:2]
"   return [line_start, column_start, line_end, column_end]
" endfun

fun! LitReplReplaceSelection(replacement) range
  " Replaces the current selection with a `replacement`, and adjusts the
  " selection registers accordingly. Returns the `replacement without change.
  let [line_start, column_start] = getpos("'<")[1:2]
  let [line_end, column_end] = getpos("'>")[1:2]
  let l:start_line = getline(line_start)
  let l:end_line = getline(line_end)
  let l:before_selection = strpart(l:start_line, 0, column_start-1)
  let l:after_selection = strpart(l:end_line, column_end)
  let l:replacement_lines = split(l:before_selection . a:replacement . l:after_selection, "\n")
  call deletebufline(bufnr(), line_start, line_end)
  call append(line_start-1, l:replacement_lines)
  let line_end2 = max([line_start, line_start+len(l:replacement_lines)-1])
  call cursor(line_end2, 1)
  call setpos("'<", [0, line_start, column_start, 0])
  call setpos("'>", [0, line_end2, len(getline(line_end2)), 0])
  return a:replacement
endfun

fun! LitReplAppend(insertion) range
  " Inserts the content at the current cursor position and moves the cursor to the
  " end of the inserted text.
  let l:line_current = getline('.')
  let l:cursor_pos = col('.')
  let l:before_cursor = strpart(l:line_current, 0, l:cursor_pos-1)
  let l:after_cursor = strpart(l:line_current, l:cursor_pos-1)
  let l:replacement_lines = split(l:before_cursor . a:insertion .  l:after_cursor, "\n")
  call deletebufline(bufnr(), line('.'))
  call append(line('.') - 1, l:replacement_lines)
  let l:last_line = line('.') + len(l:replacement_lines) - 1
  let l:last_col = len(getline(l:last_line))
  call cursor(l:last_line, l:last_col)
  return a:insertion
endfun

fun! LitReplReplaceCurrentFile(replacement) range
  " Replaces the content of the current file with the multi-line replacement
  " string
  %delete _
  call append(0, split(a:replacement, "\n"))
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

fun! LitReplAIQuery(q, paster_fn) range
  " Construct an AI prompt out of the (1) user-provided argument string (2) user
  " input (3) visual selection if the prompt is empty up to now or if `/S`
  " is found in the text (4) the contents of the current file, if `/F` is found
  " in the text.
  "
  " The prompt is then pased to the AI interpreter and the `paster_fn` is called
  " to paste the result.
  "
  " The function returns the exit code of the `litrepl eval-code` along with the
  " result of the `paster_fn` call. See `LitReplReplaceSelection` for
  " `paster_fn` example.
  if len(trim(a:q))>0
    let prompt = a:q
  else
    let prompt = input(
          \"Hint: type /S to insert the selection, ".
          \"type /F to insert current file, ".
          \"empty line uses the selection\n".
          \"Your question: ")
  endif
  if len(trim(prompt)) == 0
    let prompt = "/S"
  endif
  let prompt = substitute(prompt, "/F", "/append buffer:file buffer:in\n", "g")
  let prompt = substitute(prompt, "/S", "/append buffer:sel buffer:in\n", "g")
  let selection = LitReplGetVisualSelection()
  let prompt = "".
        \ "/clear buffer:in\n".
        \ "/paste on\n".
        \ selection."\n".
        \ "/paste off\n".
        \ "/cp buffer:in buffer:sel\n".
        \ "/cp file:\"".expand('%:p')."\" buffer:file\n".
        \ prompt

  let [errcode, result] = LitReplRun('eval-code ai', prompt)
  if errcode == 0
    let result = a:paster_fn(result)
  endif
  return [errcode, result]
endfun

if !exists(":LAI")
  command! -range -bar -nargs=* LAI call LitReplAIQuery(<q-args>, function('LitReplReplaceSelection'))
endif

let g:litrepl_extras_loaded = 1
