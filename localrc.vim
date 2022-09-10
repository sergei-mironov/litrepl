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

nnoremap <F5> :LitEval1<CR>
nnoremap <F6> :LitEvalWait1<CR>
nnoremap <F9> :unlet g:litrepl_bin<CR>:unlet g:litrepl_loaded<CR>:runtime plugin/litrepl.vim<CR>

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
    execute "VimtexReload"
    set conceallevel=0
    nnoremap <F5> :LitEval1<CR>:w<CR>:VimtexView<CR>
    nnoremap <F2> :w<CR>
endif

