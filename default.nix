{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let
  local = rec {

    inherit (pkgs) lib stdenv fetchFromGitHub imagemagick makeWrapper cloc
    gnumake socat latexrun;

    callPackage = pkgs.lib.callPackageWith collection;

    python = pkgs.python3;

    lark-parser112 = pp : (pp.lark.overrideAttrs (o : rec {
      version = "1.1.2";
      src = pkgs.fetchFromGitHub {
        owner = "lark-parser";
        repo = "lark";
        rev = version;
        sha256 = "sha256:02sdg8zppdh2hlhmyn776bfqikxm42hg27c7jj9h5a37455c6mk3";
      };
    }));

    mypython = python.withPackages (
      pp: let
        pylsp = pp.python-lsp-server;
        pylsp-mypy = pp.pylsp-mypy.override { python-lsp-server=pylsp; };
      in with pp; [
        pylsp
        pylsp-mypy
        setuptools
        setuptools_scm
        ipython
        hypothesis
        pytest
        pytest-mypy
        wheel
        (lark-parser112 pp)
        twine
        sympy
        tqdm
        matplotlib
        numpy
      ]
    );

    litrepl = (py : py.pkgs.buildPythonApplication {
      pname = "litrepl";
      version = "9999";
      src = builtins.filterSource (
        path: type: !( baseNameOf path == "build" && type == "directory" ) &&
                    !( baseNameOf path == "dist" && type == "directory" ) &&
                    !( ((builtins.match "_[^_]*" (baseNameOf path)) != null)) &&
                    !( ((builtins.match "README.md" (baseNameOf path)) != null)) &&
                    !( ((builtins.match "default.nix" (baseNameOf path)) != null)) &&
                    !( baseNameOf path == "result" )
        ) ./.;
      pythonPath = with py.pkgs; [
        (lark-parser112 py.pkgs) tqdm setuptools_scm
      ];
      nativeBuildInputs = with pkgs; [ git ];
      checkInputs = with pkgs; [
        socat which py.pkgs.ipython
      ];
      checkPhase = ''
        CWD=`pwd`
        LITREPL="python $CWD/python/bin/litrepl" \
        LITREPL_ROOT=`pwd`/python \
        LITREPL_TEST=y \
        sh ${./sh/test.sh}
      '';

      # TODO: re-enable
      doCheck = true;
    });

    mytexlive =
      (let
        mytexlive = pkgs.texlive.override { python3=mypython; };
      in
        mytexlive.combine {
          scheme-medium = mytexlive.scheme-medium;
          inherit (mytexlive) fvextra upquote xstring pgfopts currfile
          collection-langcyrillic makecell ftnxtra minted catchfile framed
          pdflscape environ trimspaces mdframed zref needspace import
          beamerposter qcircuit xypic standalone preview amsmath thmtools
          tocloft tocbibind varwidth beamer tabulary ifoddpage relsize;
        }
      );

    shell-dev = pkgs.mkShell {
      name = "shell-dev";
      buildInputs = [
        cloc
        gnumake
        socat
        latexrun
        mypython
        mytexlive
      ];
      shellHook = with pkgs; ''
        if test -f ./env.sh ; then
          . ./env.sh
          export QT_QPA_PLATFORM_PLUGIN_PATH=`echo ${pkgs.qt5.qtbase.bin}/lib/qt-*/plugins/platforms/`
        fi
      '';
    };

    vim-litrepl = (py : pkgs.vimUtils.buildVimPluginFrom2Nix {
      pname = "vim-litrepl";
      version = "9999";
      src = builtins.filterSource (
        path: type: !( baseNameOf path == "bin" && type == "directory" )) ./vim;
      postInstall = ''
        mkdir -pv $target/bin
        ln -s ${pkgs.socat}/bin/socat $target/bin/socat
        ln -s ${litrepl py}/bin/litrepl $target/bin/litrepl
      '';
    });

    vim-terminal-images = pkgs.vimUtils.buildVimPluginFrom2Nix rec {
      name = "vim-terminal-images";
      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = name;
        rev = "ccb7bd161e3a87af3305bf781481f908d58ad0fa";
        sha256 = "sha256:0f8j0dqhhrkys3yk0cwh1jhp3gswbl349fd9igzaab32h17lgni3";
      };
    };

    tupimage = stdenv.mkDerivation {
      name = "tupimage";

      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = "tupimage";
        rev = "b3c77d43cd4edd9c3bb570676059d259980b608b";
        sha256 = "sha256:0v477gizq72pcghi65m9vb9cxzzkcxizc3cpz3dldfaqpancz7i4";
      };

      buildInputs = [ makeWrapper ];

      buildCommand = ''
        mkdir -pv $out/bin
        cp -r -v $src/tupimage $out/bin
        chmod +x $out/bin/tupimage
        wrapProgram "$out/bin/tupimage" \
          --prefix PATH : "${imagemagick}/bin"
      '';
    };

    vim-test = pkgs.vim_configurable.customize {
      name = "testvim";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-litrepl
        ];
      };

      vimrcConfig.customRC = ''
      '';
    };

    grechanik-st = pkgs.st.overrideDerivation (old:{
      pname = "grechanik-st";
      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = "st";
        rev = "e4c6d7145771319518e211112f702ec380b8bda0";
        sha256 = "sha256:0f6w9hjdp1jh6s4bmpqbc210ph4vdk69fdwqy9zfy5d3fg1kc28n";
      };
      buildInputs = old.buildInputs ++ [pkgs.imlib2.dev];
      preBuild = ''
        cp ${./nix/st-config.def.h} config.def.h
      '';
    });

    vimtex-local = pkgs.vimPlugins.vimtex.overrideAttrs (old: {
      version = "master";
      src = ./modules/vimtex;
    });

    vim-demo = (py : pkgs.vim_configurable.customize {
      name = "vim-demo";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-colorschemes
          (vim-litrepl py)
          vimtex-local
          vim-terminal-images
          vim-markdown
          nerdtree
        ];
      };

      vimrcConfig.customRC = ''
        colorscheme blackboard
        syntax on
        filetype plugin indent on
        set backspace=indent,eol,start
        set wrap
        set conceallevel=0
        set textwidth=80
        set foldmethod=marker
        set foldcolumn=0

        hi Pmenu ctermbg=258

        function! Ident(ident_spaces)
          let &expandtab=1
          let &shiftwidth=a:ident_spaces
          let &tabstop=a:ident_spaces
          let &cinoptions="'g0,(".a:ident_spaces
          let &softtabstop=a:ident_spaces
        endfunction
        call Ident(2)

        vnoremap "a "ay
        vnoremap "b "by
        vnoremap "c "cy
        vnoremap "d "dy
        vnoremap "e "ey

        nnoremap "a "ap
        nnoremap "b "bp
        nnoremap "c "cp
        nnoremap "d "dp
        nnoremap "e "ep

        nnoremap "A "aP
        nnoremap "B "bP
        nnoremap "C "cP
        nnoremap "D "dP
        nnoremap "E "eP

        vnoremap y "+y
        vnoremap d "+d
        vnoremap c "+c
        nnoremap Y "+y$
        nnoremap D "+D
        nnoremap yy "+yy
        nnoremap yw "+yw
        nnoremap dd "+dd
        nnoremap cc "+cc
        vnoremap p "+p
        nnoremap p "+p
        nnoremap P "+P


        " Save
        nnoremap <F2> :noh<CR>:w!<CR>
        inoremap <F2> <ESC>:noh<CR>:w!<CR>
        nnoremap <F5> :LitEval1<CR>
        nnoremap <F6> :LitEvalLast1<CR>

        " vim-terminal-images
        let g:terminal_images_command = "${tupimage}/bin/tupimage"
        " let g:terminal_images_max_columns=5
        nnoremap gi <Esc>:TerminalImagesShowUnderCursor<CR>

        " VimTex
        let g:tex_flavor = 'latex'
        let g:vimtex_view_method = 'zathura'
        let g:vimtex_quickfix_mode=0
        let g:vimtex_format_enabled=1
        let g:vimtex_compiler_latexmk = {
           \ 'build_dir' : "",
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
        let g:vimtex_syntax_packages = { 'litrepl' : { 'load' : 2 } }


        " vim-markdown
        let g:vim_markdown_folding_disabled = 1
        let g:vim_markdown_new_list_item_indent = 2
        let g:vim_markdown_auto_insert_bullets = 0
        let g:vim_markdown_conceal = 0
        let g:vim_markdown_conceal_code_blocks = 0
      '';
    });

    vim-plug = pkgs.vim_configurable.customize {
      name = "vim-plug";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          (vim-plug.overrideAttrs (old: {
            postInstall = ''
              mkdir -pv $target/autoload
              ln -s $target/plug.vim $target/autoload
            '';
          }))
        ];
      };
      vimrcConfig.customRC = ''
        runtime! plug.vim

        call plug#begin($HOME.'/_vim')
        Plug 'https://github.com/grwlf/litrepl.vim' , { 'rtp': 'vim' }
        call plug#end()

        let $PATH="${pkgs.socat}/bin:${litrepl python}/bin:".$PATH
      '';
    };

    shell-demo = pkgs.mkShell {
      name = "shell-demo";
      buildInputs = [
        (vim-demo python)
        latexrun
        mytexlive
        grechanik-st
        (litrepl python)
      ] ++ (with pkgs ; [
        peek
      ]);
      shellHook = with pkgs; ''
        export PS1="\n[DEMO] \[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] "
      '';
    };

    shell = shell-dev;

    collection = rec {
      inherit shell shell-dev shell-demo vim-litrepl vim-test vim-demo
      grechanik-st vimtex-local;

      litrepl = litrepl mypython;
    };
  };

in
  local.collection


