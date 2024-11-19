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

fun! LitReplAISelection(q) range
  " Construct an AI prompt out of the user input [1], the selection [2] and the
  " current file [3]. Replace the selection with the output.
  if len(trim(a:q))>0
    let input = a:q
  else
    let input = input(
          \"Hint: type /S to insert the selection, ".
          \"type /F to insert current file, ".
          \"empty line uses the selection\n".
          \"Your question: ")
  endif
  if input == ''
    let input = "/S"
  endif
  let input = substitute(input, "/F", "/append buffer:file buffer:in\n", "g")
  let input = substitute(input, "/S", "/append buffer:sel buffer:in\n", "g")
  let selection = LitReplGetVisualSelection()
  let prompt = "".
        \ "/clear buffer:in\n".
        \ "/paste on\n".
        \ selection."\n".
        \ "/paste off\n".
        \ "/cp buffer:in buffer:sel\n".
        \ "/cp file:\"".expand('%:p')."\" buffer:file\n".
        \ input

  let [errcode, result] = LitReplRun('eval-code ai', prompt)
  if errcode == 0
    call LitReplReplaceSelectionWith(result)
  endif
  return [errcode, result]
endfun

if !exists(":LAI")
  command! -range -bar -nargs=* LAI call LitReplAISelection(<q-args>)
endif

let g:litrepl_extras_loaded = 1
