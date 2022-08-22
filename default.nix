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
      pythonPath = [
        (lark-parser112 python.pkgs) python.pkgs.setuptools_scm
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
      doCheck = false;
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

    vim-litrepl = pkgs.vimUtils.buildVimPluginFrom2Nix {
      pname = "vim-litrepl";
      version = "9999";
      src = ./vim;
      postInstall = ''
        mkdir -pv $target/bin
        ln -s ${pkgs.socat}/bin/socat $target/bin/socat
        ln -s ${litrepl}/bin/litrepl $target/bin/litrepl
      '';
    };

    testvim = pkgs.vim_configurable.customize {
      name = "testvim";

      vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
        start = [
          vim-litrepl
        ];
      };

      vimrcConfig.customRC = ''
      '';
    };

    plugvim = pkgs.vim_configurable.customize {
      name = "plugvim";

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
      inherit shell litrepl testvim plugvim;
    };
  };

in
  local.collection


