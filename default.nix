{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let
  lib = pkgs.lib;

  local = rec {
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
      ]
    );

    litrepl = python.pkgs.buildPythonApplication {
      pname = "litrepl";
      version = "9999";
      src = builtins.filterSource (
        path: type: !( baseNameOf path == "build" && type == "directory" ) &&
                    !( baseNameOf path == "dist" && type == "directory" ) &&
                    !( ((builtins.match "_[^_]*" (baseNameOf path)) != null)) &&
                    !( baseNameOf path == "result" )
        ) ./.;
      pythonPath = with python.pkgs; [
        (lark-parser112 python.pkgs) tqdm
      ];
      nativeBuildInputs = with pkgs; [ git ];
      checkInputs = with pkgs; [
        socat which python.pkgs.ipython
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
    };

    shell = pkgs.mkShell {
      name = "shell";
      buildInputs = with pkgs; [
        cloc
        gnumake
        socat
        latexrun
        ] ++ [
        mypython
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
        )
      ];
      shellHook = with pkgs; ''
        if test -f ./env.sh ; then
          . ./env.sh
          export QT_QPA_PLATFORM_PLUGIN_PATH=`echo ${pkgs.qt5.qtbase.bin}/lib/qt-*/plugins/platforms/`
        fi
      '';
    };

    litrepl-vim = pkgs.vimUtils.buildVimPluginFrom2Nix {
      pname = "litrepl-vim";
      version = "9999";
      src = ./vim;
      postInstall = ''
        mkdir -pv $target/bin
        ln -s ${pkgs.socat}/bin/socat $target/bin/socat
        ln -s ${litrepl}/bin/litrepl $target/bin/litrepl
      '';
    };

    vim-test = pkgs.vim_configurable.customize {
      name = "testvim";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          litrepl-vim
        ];
      };

      vimrcConfig.customRC = ''
      '';
    };

    vim-demo = pkgs.vim_configurable.customize {
      name = "vim-demo";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-colorschemes
          litrepl-vim
          vimtex
        ];
      };

      vimrcConfig.customRC = ''
        colorscheme blackboard
        syntax on
        filetype plugin indent on

        " Save
        nnoremap <F2> <ESC>:noh<CR>:w!<CR>
        inoremap <F2> <ESC>:noh<CR>:w!<CR>

        " VimTex
        let g:tex_flavor = 'latex'
        let g:vimtex_view_method = 'zathura'
        let g:vimtex_quickfix_mode=0
        let g:vimtex_format_enabled=1
      '';
    };

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

        let $PATH="${pkgs.socat}/bin:${litrepl}/bin:".$PATH
      '';
    };

    collection = rec {
      inherit shell litrepl vim-test vim-demo;
    };
  };

in
  local.collection


