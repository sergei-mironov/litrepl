## Installation

The Github repository hosts the Litrepl tool, a standalone command-line
application and an interface plugin for the Vim editor. The author's preferred
installation method is using Nix, but if you choose not to use it, you'll need
to install one or both components separately. Below, we outline several common
installation methods.

### Installing release versions from Pypi and Vim.org

1. `pip install litrepl`
2. Download the `litrepl.vim` from the vim.org
   [script page](https://www.vim.org/scripts/script.php?script_id=6117) and put it into
   your `~/.vim/plugin` folder.


### Installing latest versions from Git using Pip and Vim-Plug

1. Install the `litrepl` Python package with pip:
   ``` sh
   $ pip install --user git+https://github.com/sergei-mironov/litrepl
   $ litrepl --version
   ```
2. Install the Vim plugin by adding the following line between the
   `plug#begin` and `plug#end` lines of your `.vimrc` file:
   ```vim
   Plug 'https://github.com/sergei-mironov/litrepl' , { 'rtp': 'vim' }
   ```
   Note: `rtp` sets the custom vim-plugin source directory of the plugin.


### Installing latest versions from source using Nix

The repository offers a suite of Nix expressions designed to optimize
installation and development processes on systems that support Nix. Consistent
with standard practices in Nix projects, the [flake.nix](./static/flake.nix) file
defines the source dependencies, while the [default.nix](./static/default.nix) file
identifies the build targets.

For testing, the `vim-demo` expression is a practical choice. It includes a
pre-configured Vim setup with several related plugins, including Litrepl. To
build this target, use the command `nix build '.#vim-demo'`. Once the build is
complete, you can run the editor with `./result/bin/vim-demo`.

To add the Litrepl tool to your system profile, first include the Litrepl flake
in your flake inputs. Then, add `litrepl-release` to
`environment.systemPackages` or to your custom environment.

To include the Litrepl Vim plugin, add `vim-litrepl-release` to the `vimPlugins`
list within your `vim_configurable` expression.

Regardless of the approach, Nix will manage all necessary dependencies
automatically.

Nix are used to open the development shell, see the
[Development](./development.md) section.


### Installing latest versions from source using Pip

The Litrepl application might be installed with `pip install .` run from the
project root folder. The Vim plugin part requires hand-copying
`./vim/plugin/litrepl.vim` and `./vim/plugin/litrepl_extras.vim` to the `~/.vim`
config folder.

### Notes

The Nix-powered installation methods install the Socat tool automatically. For
other installation methods, use your system pacakge manager to install it. For
example, Ubuntu users might run `sudo apt-get install socat`.

The Python interpreter is usually installed by default, along with the `pip`
installer. To install `ipython`, you can use `pip install ipython`. For the
[aicli](https://github.com/sergei-mironov/aicli) interpreter, you can run `pip
install sm_aicli`, or refer to the project page for additional installation
methods.

