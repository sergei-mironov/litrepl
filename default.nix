{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
, src ? builtins.filterSource (
    path: type: !( baseNameOf path == "build" && type == "directory" ) &&
                !( baseNameOf path == "dist" && type == "directory" ) &&
                !( ((builtins.match "_[^_]*" (baseNameOf path)) != null)) &&
                !( ((builtins.match "README.md" (baseNameOf path)) != null)) &&
                !( ((builtins.match "default.nix" (baseNameOf path)) != null)) &&
                !( baseNameOf path == "result")) ./.
, revision ? null
, aicli ? null
} :
let
  local = rec {

    litrepl_root = src;

    version = lib.fileContents "${litrepl_root}/semver.txt";
    version_full = if revision != null then
      "${version}+g${builtins.substring 0 7 revision}" else
      version;

    inherit (pkgs) lib stdenv fetchFromGitHub imagemagick makeWrapper cloc
    gnumake socat latexrun sloc;

    callPackage = pkgs.lib.callPackageWith collection;

    python = pkgs.python3;

    lark112 = pp : (pp.lark.overrideAttrs (o : rec {
      version = "1.1.2";
      src = pkgs.fetchFromGitHub {
        owner = "lark-parser";
        repo = "lark";
        rev = version;
        sha256 = "sha256:02sdg8zppdh2hlhmyn776bfqikxm42hg27c7jj9h5a37455c6mk3";
      };
    }));

    lark119 = pp : (pp.lark.overrideAttrs (o : rec {
      pname = "lark";
      version = "1.1.9";
      src = pkgs.fetchFromGitHub {
        owner = "lark-parser";
        repo = "lark";
        rev = "refs/tags/${version}";
        hash = "sha256-pWLKjELy10VNumpBHjBYCO2TltKsZx1GhQcGMHsYJNk=";
      };
      format = "pyproject";
      nativeBuildInputs = [ pp.setuptools pp.wrapPython ];
    }));

    lark-latest = pp : pp.lark;

    lark-current = lark-latest;

    python-test = python: python.withPackages (
      pp: let
      in with pp; [
        setuptools
        # setuptools_scm
        pytest
        # pytest-mypy
        wheel
        (lark-current pp)
        tqdm
        matplotlib
        # numpy
        # bpython
        psutil
      ] ++ (if pp.pythonAtLeast "3.10" then [
        ipython
      ] else [])
    );

    python-dev = python.withPackages (
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
        (lark-current pp)
        twine
        sympy
        tqdm
        matplotlib
        numpy
        bpython
        psutil
        coverage
        (aicli.aicli pp)
        (coverage-badge pp)
      ]
    );

    python-release = pkgs.python3.withPackages (
      pp: with pp; [
        (lark-current pp)
        psutil
      ]
    );

    python-demo = pkgs.python3.withPackages (
      pp: with pp; [
        (lark-current pp)
        psutil
        ipython
        tqdm
      ]
    );

    coverage-badge = (pp: with pp; buildPythonPackage rec {
      pname = "coverage_badge";
      version = "1.1.2";

      format = "setuptools";
      build-system = [
        setuptools
        wheel
      ];
      dependencies = [
        setuptools
        coverage
      ];
      src = fetchPypi {
        inherit pname version;
        sha256 = "sha256-/n7Vijty2thaVTtkqZ6WPeo4R9zQuN3Ss4oAMzYYZCw=";
      };
    });

    coverage-badge-release = (coverage-badge python-release.pkgs);

    litrepl = (py : py.pkgs.buildPythonApplication {
      pname = "litrepl";
      inherit version;
      inherit src;
      LITREPL_REVISION = revision;
      LITREPL_ROOT = src;
      propagatedBuildInputs = [(lark-current py.pkgs) py.pkgs.psutil pkgs.socat];
      nativeCheckInputs = with pkgs; [
        socat py.pkgs.ipython py.pkgs.tqdm which git vim
        aicli.python-aicli py.pkgs.coverage (coverage-badge py.pkgs)
      ];
      # We cut off the python PATH to allow users to use litrepl in custom
      # Python environments
      postFixup = ''
        sed -i '/PATH.*python/d' $out/bin/litrepl
      '';
      checkPhase = ''
        LITREPL_BIN="$out/bin" \
        LITREPL_ROOT=`pwd` \
        ${./sh/runtests.sh}
      '';

      doCheck = true;
    });

    litrepl-pypi = (python: python.pkgs.buildPythonPackage rec {
      pname = "litrepl";
      inherit version;
      propagatedBuildInputs = [(lark-current python.pkgs) pkgs.socat python.pkgs.psutil];
      src = python.pkgs.fetchPypi {
        inherit pname version;
        sha256 = "sha256-JA/CW8mfRqRQWc35qQx4JgZ/iLmopPTJDO8rIqtBB/U=";
        # sha256 = "sha256-+ass/WI8dfA+a5fBGcCYCr5xswC7uWVfd2oCsp1Zt48=";
        # sha256 = "sha256-LI4k6anvK9MMqz0n8M8l5W5v3qM0i5TN9ho2QWwIGjQ=";
        # sha256 = "sha256-yrnqBSH+idosum/97Gwz4cB36hsggrMfOtoGspiPHb8=";
        # sha256 = "sha256-B1qDAksYPQm+hkG7T79sMEKgZ9mM4ncEBaEq4qye/bo=";
        # sha256 = "sha256-kf/gx5f7VIKfDBxpTG/E1ghdBGRulbFoVHoNqT/FoSM=";
        # sha256 = "sha256-oWcX+5GFL3sDGKYYYlJoeglBdcufro6Sk9KZSJMt0t0=";
        # sha256 = "sha256-eOr+64tSPXPUrqI9w4UUNLtvf0ziE/vHmuU5050VS1s=";
        # sha256 = "sha256-Ex06917+Grhhv8hGEr59CUK0+5tsQ6+wNv+7to2WDrg=";
        # sha256 = "sha256-tiNqmVMM3JttYc8LNnmMdxw6cenogCAhFu9feVMsnq4=";
        # sha256 = "sha256:0vq2igzfi3din1fah18fzp7wdh089hf28s3lwm321k11jhycqgy9";
      };
    });

    mytexlive =
      (let
        mytexlive = pkgs.texlive.override { python3=python-dev; };
      in
        mytexlive.combine {
          scheme-medium = mytexlive.scheme-medium;
          inherit (mytexlive) fvextra upquote xstring pgfopts currfile
          collection-langcyrillic makecell ftnxtra minted catchfile framed
          pdflscape environ trimspaces mdframed zref needspace import
          beamerposter qcircuit xypic standalone preview amsmath thmtools
          tocloft tocbibind varwidth beamer tabulary ifoddpage relsize svg
          transparent;
        }
      );

    shell-dev = pkgs.mkShell {
      name = "shell-dev";
      buildInputs = [
        cloc
        gnumake
        socat
        latexrun
        python-dev
        mytexlive
        pkgs.pandoc
        pkgs.inkscape
        sloc
      ];
      shellHook = with pkgs; ''
        if test -f ./env.sh ; then
          . ./env.sh
          export QT_QPA_PLATFORM_PLUGIN_PATH=`echo ${pkgs.qt5.qtbase.bin}/lib/qt-*/plugins/platforms/`
        fi
      '';
    };

    shell-test = pkgs.mkShell {
      name = "shell-test";
      buildInputs = [
        gnumake
        socat
        (python-test pkgs.python39)
        (python-test pkgs.python310)
        (python-test pkgs.python312)
      ];
      shellHook = with pkgs; ''
        if test -f ./env.sh ; then
          . ./env.sh
          export QT_QPA_PLATFORM_PLUGIN_PATH=`echo ${pkgs.qt5.qtbase.bin}/lib/qt-*/plugins/platforms/`
        fi
      '';
    };

    vim-litrepl_ = (litrepl: py : pkgs.vimUtils.buildVimPluginFrom2Nix rec {
      pname = "vim-litrepl";
      inherit version;
      src = builtins.filterSource (
        path: type: !( baseNameOf path == "bin" && type == "directory" )) ./vim;
      postInstall = ''
        mkdir -pv $target/bin
        sed -i "s/version-to-be-filled-by-the-packager/${version_full}/g" \
          $target/plugin/litrepl.vim
        ln -s ${pkgs.socat}/bin/socat $target/bin/socat
        ln -s ${litrepl py}/bin/litrepl $target/bin/litrepl
      '';
    });

    vim-litrepl = py: vim-litrepl_ litrepl py;
    vim-litrepl-pypi = py: vim-litrepl_ litrepl-pypi py;

    vim-terminal-images = pkgs.vimUtils.buildVimPluginFrom2Nix rec {
      name = "vim-terminal-images";
      # https://github.com/sergei-grechanik/vim-terminal-images/commits/master
      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = name;
        rev = "8e617d76bbd2555d466c36a783835e63001135e9";
        sha256 = "sha256-/CucaNiVkgvMuhtz8tULn3HGAgjq7d/cu4pIo0I6wlI=";
      };
    };

    tupimage = stdenv.mkDerivation {
      name = "tupimage";

      # https://github.com/sergei-grechanik/tupimage/commits/main
      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = "tupimage";
        rev = "276d4ae07a79fe417f0419db8ece00ad3df5d911";
        sha256 = "sha256-BQoclsLXFjMMjOQIXdGSjlSq+BrNRuz09LoBtmcEkRY=";
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
          vim-litrepl-release
        ];
      };

      vimrcConfig.customRC = ''
      '';
    };

    grechanik-st = pkgs.st.overrideDerivation (old:{
      pname = "grechanik-st";
      # https://github.com/sergei-grechanik/st/commits/graphics
      src = fetchFromGitHub {
        owner = "sergei-grechanik";
        repo = "st";
        rev = "1ccdc65104d71776da1ed4c4c6246b35ece0ee1e";
        sha256 = "sha256-2qNCWn0xLplq+vKvCSkp/hipSer/K4JRRCHyKj3NJFI=";
      };
      buildInputs = old.buildInputs ++ [pkgs.imlib2.dev];
      preBuild = ''
        cp ${./nix/st-config.def.h} config.def.h
      '';
    });

    grechanik-st-light = pkgs.st.overrideDerivation (old:{
      pname = "grechanik-st";

      src = fetchFromGitHub {
        owner = "grwlf";
        repo = "st";
        rev = "local";
        sha256 = "sha256-6WJncoeJRwhDSiurLgoTe5lpIShcOWyYKcBOKulnJXQ=";
      };
      buildInputs = old.buildInputs ++ [pkgs.imlib2.dev];
      preBuild = ''
        cp ${./nix/st-config-light.h} config.def.h
      '';
      CFLAGS = "-DCOLORSCHEME=2";
    });

    vimtex-local = pkgs.vimPlugins.vimtex.overrideAttrs (old: {
      version = "master";
      src = ./modules/vimtex;
    });

    vim-demo = pkgs.vim_configurable.customize {
      name = "vim-demo";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-colorschemes
          vim-litrepl-release-pypi
          # vimtex-local
          vimtex
          vim-terminal-images
          vim-markdown
          nerdtree
          changeColorScheme-vim
        ];
      };

      vimrcConfig.customRC = ''
        filetype plugin indent on
        syntax on
        " colorscheme C64
        " colorscheme Tomorrow-Night-Blue
        colorscheme 256-jungle
        set backspace=indent,eol,start
        set wrap
        set conceallevel=0
        set textwidth=53
        set foldmethod=marker
        set foldcolumn=0
        set autoread
        set noswapfile

        hi Pmenu ctermbg=258

        function! Ident(ident_spaces)
          let &expandtab=1
          let &shiftwidth=a:ident_spaces
          let &tabstop=a:ident_spaces
          let &cinoptions="'g0,(".a:ident_spaces
          let &softtabstop=a:ident_spaces
        endfunction
        call Ident(2)

        function! SynClear(name)
          if hlexists(a:name)
            execute "syntax clear ".a:name
          end
        endfun

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

        nnoremap <F2> :noh<CR>:w!<CR>
        inoremap <F2> <ESC>:noh<CR>:w!<CR>
        nnoremap <F5> :LEval<CR>
        nnoremap <F9> :call NextColorScheme()<CR>:colorscheme<CR>
        nnoremap <F10> :call PreviousColorScheme()<CR>:colorscheme<CR>

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
           \ }
        let g:vimtex_syntax_packages = { 'litrepl' : { 'load' : 2 } }


        " vim-markdown
        let g:vim_markdown_folding_disabled = 1
        let g:vim_markdown_new_list_item_indent = 2
        let g:vim_markdown_auto_insert_bullets = 0
        let g:vim_markdown_conceal = 0
        let g:vim_markdown_conceal_code_blocks = 0
      '';
    };

    vim-plug-test = pkgs.vim_configurable.customize {
      name = "vim-plug-test";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          # vim-plug # <--- Does not work as-is, so the below override is required.
          (vim-plug.overrideAttrs (old: {
            postInstall = ''
              mkdir -pv $target/autoload
              ln -s $target/plug.vim $target/autoload
            '';
          }))
        ];
      };
      vimrcConfig.customRC = ''
        call plug#begin($HOME.'/_vim')
        Plug 'https://github.com/sergei-mironov/litrepl.vim' , { 'rtp': 'vim' }
        call plug#end()

        " Setting PATH is a custom requirement of the above Litrepl plugin
        let $PATH="${pkgs.socat}/bin:${litrepl python}/bin:".$PATH
      '';
    };

    shell-screencast = pkgs.mkShell {
      name = "shell-screencast";
      buildInputs = [
        vim-demo
        latexrun
        mytexlive
        grechanik-st
        litrepl-release-pypi
        python-demo
      ] ++ (with pkgs ; [
        # obs-studio
        peek
        tmux
        xdotool
        xorg.xwininfo
        (aicli.aicli python-release.pkgs)
      ]);
      shellHook = with pkgs; ''
        export PS1="\n[DEMO] \[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] "
        # exec ${grechanik-st}/bin/st
        CWD=$(pwd)
        export PATH=$CWD/sh:$CWD/python/bin:$PATH
      '';
    };

    shell = shell-dev;


    litrepl-dev = litrepl python-dev;
    litrepl-release = litrepl python-release;
    litrepl-release-pypi = litrepl-pypi python-release;
    vim-litrepl-release = vim-litrepl python-release;
    vim-litrepl-release-pypi = vim-litrepl-pypi python-release;
    aicli-release = aicli.aicli python-release.pkgs;

    collection = rec {
      inherit aicli;
      inherit pkgs shell shell-dev shell-screencast shell-test
      vim-litrepl-release vim-test vim-demo vim-plug-test grechanik-st
      vimtex-local litrepl-release litrepl-dev litrepl-release-pypi
      vim-litrepl-release-pypi python-release coverage-badge-release
      aicli-release;
    };
  };

in
  local.collection


