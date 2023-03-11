Development
===========

Cloning
-------

1. `git clone --recursive https://github.com/grwlf/litrepl.vim; cd litrepl.vim`
2. Enter the development environment
   * (Nix/NixOS systems) `nix develop`
   * (Other Linuxes) `. env.sh`
     Read the warnings and install missing packages if required. The
     environment script will add `./sh` and `./python` folders to the current
     shell's PATH/PYTHONPATH.  The former folder contains the back-end script, the
     latter one contains the Python library.
3. (Optional) Run `test.sh`
4. Run the `vim_litrepl_dev` (a thin wrapper around Vim) to run the Vim with the
   LitREPL plugin from the `./vim` folder.

Nix hints
---------

[flake.nix](./flake.nix) defines the Nix-flake expression. A number of
subexpressions are available for both individual components of the project and
several flavors of shells.

To enter the main development shell, execute
``` sh
$ nix develop
```

To build individual componets, run the `nix build` command passing it the name
of expression to build:

``` sh
$ nix build '.#litrepl-release'
```

The list of expressions includes:

* `litrepl-release` - Litrepl script and Python lib
* `litrepl-release-pypi` - Litrepl script and Python lib
* `vim-litrepl-release` - Vim with locally built litrepl plugin
* `vim-litrepl-release-pypi` - Vim with litrepl plugin built from PYPI
* `vim-test` - A minimalistic Vim with a single litrepl plugin
* `vim-demo` - Vim with litrepl for recording screencasts
* `vim-plug` - vim configured to use the Plug manager
* `shell-dev` - The main development shell
* `shell-demo` - The shell for recording demonstrations

Hints
-----

A useful keymapping to reload the plugin:

```vim
nnoremap <F9> :unlet g:litrepl_bin<CR>:unlet g:litrepl_loaded<CR>:runtime plugin/litrepl.vim<CR>
```

To view debug messages, set

```vim
let g:litrepl_debug = 1
let g:litrepl_always_show_stderr = 1
```

