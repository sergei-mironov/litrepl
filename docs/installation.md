## Installation

The Github repository hosts the Litrepl tool, a standalone command-line
application and an interface plugin for the Vim editor. The author's preferred
installation method is using Nix, if you choose not to use it, you'll need to
install one or both components separately. Below, we outline several common
installation methods.

For the installation of Litrepl Vim plugin, which is also a part of the project,
check the [Vim plugin](./usage/vim-plugin.md) section.

### Requirements

* **POSIX-compatible OS**, typically a Linux. The tool relies on POSIX
  operations, notably pipes, and depends on certain Shell commands.
* **lark-parser** and **psutil** Python packages. These should be handled
  automatically by the below installation methods.
* **[Socat](http://www.dest-unreach.org/socat/)** (Optional) Needed for
  `litrepl repl` and Vim's `LTerm` commands to work. In most operating systems
  Socat should be installed separately.

### Installing release versions from Pypi

1. Install the latest Litrepl from Pypi repository
   ``` sh
   $ pip install litrepl
   ```
2. Optionally, install the `socat` tool using your system package manager.

### Installing latest versions from Git using Pip

1. Install the `litrepl` Python package with pip:
   ``` sh
   $ pip install --user git+https://github.com/sergei-mironov/litrepl
   $ litrepl --version
   ```
2. Optionally, install the `socat` tool using your system package manager.

For more development dependencies, check the `sh/install_deps_ubuntu.sh` in the
source code repository.

### Installing latest versions from source using Nix

The repository offers a suite of Nix expressions designed to optimize
installation and development processes on systems that support Nix. Consistent
with standard practices in Nix projects, the [flake.nix](./static/flake.nix) file
defines the source dependencies, while the [default.nix](./static/default.nix) file
identifies the targets Nix expressions.

For testing, the `vim-demo` expression is a practical choice. It includes a
pre-configured Vim setup with several related plugins, including Litrepl. Once
the build is complete, you can run the Vim editor using the
`./result/bin/vim-demo` command. The overall procedure looks as follows:

``` sh
$ git clone https://github.com/sergei-mironov/litrepl
$ cd litrepl
$ nix build '.#vim-demo'
  # ... Nix builds Litrepl and a pre-configured Vim editor.
$ ./result/bin/vim-demo
```

To build the release version of Litrepl, build the `litrepl-release` target. The
`./result` will point to the resulting Litrepl tree.

``` sh
$ nix build '.#litrepl-release'
$ ./result/bin/litrepl --version
# ...
```

Wiring Litrepl to your NixOS system depends on your particular system's
organisation.  Typically, for updating system profile, first include the Litrepl
flake in your system flake as an input. Then, add the `litrepl-release`
expression to `environment.systemPackages` or to your custom environment.

``` nix
# File: flake.nix
inputs = {
    # ...
    vim-litrepl = {
      url = "github:sergei-mironov/litrepl.vim";
      # Also consider wiring your system "nixpkgs" input
      # inputs.nixpkgs.follows = "nixpkgs";
    };
    # ...
}

# File: configuration.nix
environment.systemPackages = with pkgs; [
    # ...
    vim-litrepl.litrepl-release
    # ...
];
```

Nix will manage all necessary dependencies automatically.

For the full list of expressions which includes developement shells, see the
[Development](./development.md) section.


### Installing latest versions from source using Pip

The Litrepl application might be installed with `pip install .` run from the
project root folder.

### Notes

#### Optional Socat tool

The Nix-powered installation methods install the Socat tool automatically. For
other installation methods, use your system package manager to install it. For
example, Ubuntu users might run `sudo apt-get install socat`.

#### Python interpreters

The Python interpreter is usually installed by default, along with the `pip`
installer. To install `ipython`, you can use `pip install ipython`.

#### Aicli interpreter

A GNU Readline-based application for interacting with chat-oriented AI models,
which Litrep supports as the interpret for `ai` code sections.

For the details, please check the
[aicli](https://github.com/sergei-mironov/aicli) project page. Typically, you
can install it with `pip install sm_aicli`.

