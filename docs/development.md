## Development

Litrepl uses [Nix](https://nixos.org/nix) as its main development
framework. The file [flake.nix](./static/flake.nix) manages the source-level
dependencies required by Nix, whereas [default.nix](./static/default.nix) specifies
common build targets, including PyPI and Vim packages, demo Vim configurations,
development shells, and more.

### Building Targets

To build individual Nix expressions, execute the command `nix build '.#NAME'`,
replacing `NAME` with the actual name of the Nix expression you want to build.
If the build is successful, Nix places the results of the last build in a
symbolic link located at `./result`.

For example, to build a version of Vim pre-configured for demo, run

``` sh
$ nix build '.#vim-demo'
$ ./result/bin/vim-demo  # Run the pre-configured demo instance of Vim
```

The list of Nix build targets includes:

* `litrepl-release` - Litrepl script and Python lib
* `litrepl-release-pypi` - Litrepl script and Python lib
* `vim-litrepl-release` - Vim with locally built litrepl plugin
* `vim-litrepl-release-pypi` - Vim with litrepl plugin built from PYPI
* `vim-test` - A minimalistic Vim with a single litrepl plugin
* `vim-demo` - Vim configured to use litrepl suitable for recording screencasts
* `vim-plug` - Vim configured to use litrepl via the Plug manager
* `shell-dev` - The development shell
* `shell-screencast` - The shell for recording demonstrations, includes `vim-demo`.

See `local.collection` attribute-set in the [default.nix](./static/default.nix) for the
full list of defined targetr.

### Development Environments and Setup

The default development shell is defined in the `./default.nix` as a Nix
expression named `shell` which is the default name for development shells.
Running

``` sh
$ nix develop
```

will ask Nix to install the development dependencies and open shell.

### Testing

The `runtests.sh` script runs all tests by default, but accepts command-line
arguments for running specific tests.

<!--
``` python
print("~~~~ shell\n[ LitREPL-DEV ] $ runtests.sh --help")
!runtests.sh --help
print("~~~~")
```
-->
<!-- result -->
~~~~ shell
[ LitREPL-DEV ] $ runtests.sh --help
Usage: runtest.sh [-d] [-i I(,I)*] [-t T(,T)*]
Arguments:
  -d                        Be very verbose
  -i I, --interpreters=I    Run tests requiring interpreters matching the grep expression I
                            Run -i '?' to list all available interpreters
  -t T, --tests=T           Run tests whose names match the grep expression T
                            Run -t '?' to list all available tests
  -p P, --python=P          Use this Python interpreter to run Litrepl
                            Run -p '?' to list available python interpreters
  -c FILE, --coverage=FILE  Collect coverage results into the FILE. Defaults to
                            `.coverage` if no tests or interpreters are
                            selected, otherwize disabled.
  -c -,    --coverage=-     Disable coverage.

Examples:
  runtests.sh -t '?' -i '?'
  runtests.sh -i ipython
  runtests.sh -t 'test_eval_code|test_status' -i python
~~~~
<!-- noresult -->

### Tools for Screencast Recording

Another shell which might be useful is `shell-screencast`. This would build the
full set of Litrepl tools and makes sure that the screencasting software is
available. To enter it, specify its Nix-flake path as follows:

``` sh
$ nix develop '.#shell-screencast'
```

In the opened shell, run the `screencast.sh` and wait a second, until the script
arranges demo and recorder wondows.

``` sh
$ screencast.sh
```

`screencast.sh` accepts an optional parameter specifying the template file to
open for the recording session.

### Other Development Scenarios

The top-level [Makefile](./static/Makefile) encodes common development scenarios:

<!--
``` python
print("~~~~ shell\n[ LitREPL-DEV ] $ make help")
!make help
print("~~~~")
```
-->
<!-- result -->
~~~~ shell
[ LitREPL-DEV ] $ make help
make[1]: Entering directory '/home/grwlf/proj/litrepl.vim'
LitREPL is a macroprocessing Python library for Litrate programming and code execution
Build targets:
man:        Build a manpage
docs:       Build the MkDocs documentation
help:       Print help
test:       Run the test script (./sh/runtests.sh)
readme:     Update code sections in the README.md
wheel:      Build Python wheel (the DEFAULT target)
vimbundle:  Build Vim bundle
version:    Print the version
dist:       Build Python and Vim packages
upload:     Upload Python wheel to Pypi.org (./_token.pypi is required)
make[1]: Leaving directory '/home/grwlf/proj/litrepl.vim'
~~~~
<!-- noresult -->
