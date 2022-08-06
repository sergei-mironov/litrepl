" Set the identation size

set wrap
set conceallevel=0
set textwidth=80

function! Ident(ident_spaces)
  let &expandtab=1
  let &shiftwidth=a:ident_spaces
  let &tabstop=a:ident_spaces
  let &cinoptions="'g0,(".a:ident_spaces
  let &softtabstop=a:ident_spaces
endfunction

if &filetype == 'python'
  call Ident(2)
endif

if &filetype == 'tex'
  syn region texZone start="\\begin{shellcode}"
        \ end="\\end{shellcode}\|%stopzone\>" contains=@Spell
  syn region texZone start="\\begin{pythoncode}"
        \ end="\\end{pythoncode}\|%stopzone\>" contains=@Spell
  syn region texZone start="\\begin{pythontexcode}"
        \ end="\\end{pythontexcode}\|%stopzone\>" contains=@Spell
  try
    call TexNewMathZone("Z","eq",0)
  catch
    call vimtex#syntax#core#new_region_math('eq')
  endtry
endif

