" Set the identation size

set wrap
set conceallevel=0
set textwidth=80

" vim-markdown
" Disable buggy nested markdown
" let g:vim_markdown_fenced_languages = [ 'markdown=xxx' ]

" vimtex
let g:vimtex_compiler_latexmk = {
  \ 'build_dir' : '',
  \ 'callback' : 1,
  \ 'continuous' : 1,
  \ 'executable' : 'latexmk',
  \ 'hooks' : [],
  \ 'options' : [
  \   '-verbose',
  \   '-file-line-error',
  \   '-synctex=1',
  \   '-interaction=nonstopmode',
  \   '-latex="pdflatex -shell-escape"',
  \   '-latexoption=-shell-escape',
  \ ],
  \}

let g:vimtex_compiler_latexrun = {
  \ 'build_dir' : '',
  \ 'options' : [
  \   '--verbose-cmds',
  \   '--latex-args="-synctex=1 -shell-escape"',
  \ ],
  \}

let g:vimtex_compiler_method='latexmk'

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

nnoremap <F5> :LitEval1<CR>
nnoremap <F6> :LitEvalWait1<CR>
nnoremap <F9> :unlet g:litrepl_bin<CR>:unlet g:litrepl_loaded<CR>:runtime plugin/litrepl.vim<CR>

if &filetype == 'tex'

  if !exists("g:vimtex_reloaded")
    execute "VimtexReload"
    let g:vimtex_reloaded = 1
  end

  call vimtex#syntax#nested#include('python')
  call vimtex#syntax#core#new_region_env('texLitreplZone', 'l[a-zA-Z0-9]*code',
    \ {'contains': '@vimtex_nested_python'})

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


  set conceallevel=0
  nnoremap <F5> :LitEval1<CR>:w<CR>:VimtexView<CR>
  nnoremap <F2> :w<CR>
endif

if &filetype == 'markdwon'
endif
