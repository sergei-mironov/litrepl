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

function! LitReplReplaceSelectionWith(replacement) range
  " Replaces the current selection with a `replacement`, and adjusts the
  " selection registers accordingly.
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
endfunction

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

fun! LitReplAIQuery(q) range
  " Construct an AI prompt out of the (1) user-provided argument string (2) user
  " input (3) visual selection if the prompt is empty up to now or if `/S`
  " is found in the text (4) the contents of the current file, if `/F` is found
  " in the text.
  if len(trim(a:q))>0
    let prompt = a:q
  else
    let prompt = input(
          \"Hint: type /S to insert the selection, ".
          \"type /F to insert current file, ".
          \"empty line uses the selection\n".
          \"Your question: ")
  endif
  if prompt == ''
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
    call LitReplReplaceSelectionWith(result)
  endif
  return [errcode, result]
endfun

if !exists(":LAI")
  command! -range -bar -nargs=* LAI call LitReplAIQuery(<q-args>)
endif

let g:litrepl_extras_loaded = 1
