{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let
  local = rec {

    inherit (pkgs) lib stdenv fetchFromGitHub imagemagick makeWrapper cloc
    gnumake socat latexrun;

    callPackage = pkgs.lib.callPackageWith collection;

    python = pkgs.python38;

    lark-parser112 = pp : (pp.lark-parser.overrideAttrs (o : rec {
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
        pyls = pp.python-language-server.override { providers=["pycodestyle"]; };
        pyls-mypy = pp.pyls-mypy.override { python-language-server=pyls; };
      in with pp; [
        pyls
        pyls-mypy
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
      src = ./vim;
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
        rev = "9eb7b143ed712773f2fafab7e4c7af8d978ac927";
        sha256 = "sha256:1kqgdz7bzaj4rmj9wd9dzy6k26ngysims5j1qrhhpipmkai60bzw";
      };
    };

    tupimage = stdenv.mkDerivation {
      name = "tupimage";

      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = "tupimage";
        rev = "256a5960099e36f9429ccda1354a61de3cf0f36a";
        sha256 = "sha256:1hj98vhs4bggqgwig78fmyrinfxqwx3kbddqbiccs194pqvhvf2b";
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
    });

    vim-demo = (py : pkgs.vim_configurable.customize {
      name = "vim-demo";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-colorschemes
          (vim-litrepl py)
          vimtex
          # vim-terminal-images
          vim-markdown
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

        " VimTex
        let g:tex_flavor = 'latex'
        let g:vimtex_view_method = 'zathura'
        let g:vimtex_quickfix_mode=0
        let g:vimtex_format_enabled=1

        " vim-terminal-images
        let g:terminal_images_command = "${tupimage}/bin/tupimage"
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

    # demo-set = {
    #   inherit grechanik-st vim-demo;
    # };

    shell-demo = pkgs.mkShell {
      name = "shell-demo";
      buildInputs = [
        (vim-demo python)
        latexrun
        mytexlive
        mypython
      ] ++ (with pkgs ; [
        peek
      ]);
      # shellHook = ''
      #   if test -f ./env.sh ; then
      #     . ./env.sh
      #     export QT_QPA_PLATFORM_PLUGIN_PATH=`echo ${pkgs.qt5.qtbase.bin}/lib/qt-*/plugins/platforms/`
      #   fi
      # '';
    };

    shell = shell-dev;

    collection = rec {
      inherit shell shell-dev shell-demo vim-litrepl vim-test vim-demo
      grechanik-st;

      litrepl = litrepl mypython;
    };
  };

in
  local.collection


