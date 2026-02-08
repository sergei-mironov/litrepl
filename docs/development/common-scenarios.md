## Common scenarios

<!-- BEGIN OF CONTRIBUTING.md -->

Litrepl uses [Nix](https://nixos.org/nix) as its main development
framework. The file [flake.nix](../static/flake.nix) manages the source-level
dependencies required by Nix, whereas [default.nix](../static/default.nix) specifies
common build targets, including PyPI and Vim packages, demo Vim configurations,
development shells, and more.

### Environment setup

The default development shell is defined in the `./default.nix` as a Nix
expression named `shell` which is the default name for development shells.
Running

``` sh
$ nix develop
```

will ask Nix to install the development dependencies and open the shell.

### Directory structure

The project is organized in the following way:

The code:

* `python` contains most of the Litrepl code.  `python/litrepl` is where most of
  the code reside, `python/bin` is the entry point.
* `vim` contains the code for the Litrepl Vim plugin.
* `semver.txt` contains the current Litrepl version, `semver_released.txt`
  tracks the last Litrepl version uploaded to Pypi.

The environment:

* `vimrc` contains vim configurations used by the author for the development.
* `sh` contains vaious shell scripts and tests for the development.
* `env.sh` contains developement shell definitions. Notably, it adds `python` to
  the `PYTHONPATH`, `sh` to `PATH`, etc.
* `Makefile` encodes most of the developmemnt actions. `make help` will print
  the list of them.
* `flake.nix`, `default.nix`, `shell.nix` Nix expressions describing software
  build targets and dependencies.

### Coding style

The author uses his favorite yet unusual Python coding style for this project,
the following guidelines are applied:

* Use 2-space indentation for everything.
* Use CamelCase for class names and snake_case for function names
* Use explicit `from <module> import <function>` rather than `import <module>`
  for importing.
* Insert type annotations where possible, use old-style upper-case type names
  from the `typing` module.
* Avoid spaces where possible with the following exceptions:
  - Import name lists
  - Function argument declarations

### Running tests

The [sh/runtests.sh](../static/sh/runtests.sh) script runs all or selected tests.
Note, that Litrepl distinguishes the Python interpreter used to run the `litrepl`
script (`-p` argument) from the Python interpreters used to run the code
sections (`-i` argument).  By default, `runtest.sh` runs the litrepl script with
the `python` interpreter (whatever it is, leaving the OS to decide) and iterates
over all visible Python interpreters for running code sections.


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

The project Makefile provides a couple of phony targets for testing: `make test`
runs the testing with all default parameters (effectively checking all Python
interpreters available in PATH), while the `make test-small` makes a run with
just the default system Python and IPython interpreters only.

### Updating version

We follow the https://semver.org/ guidelines for setting the package version.

The `./semver.txt` file contains the version string. Please update it according to
the nature of changes and include into the pull request.

<!-- END OF CONTRIBUTING.md -->

### Coverage

Coverage is performed after the full testing cycle.

The latest coverage report is [available](../coverage.md).

### Github CI

The [.github/workflows/testing.yaml](../static/.github/workflows/testing.yaml)
rule set instructs Github CI to run the set of `test-small` tests for some
versions of Python interpreter. The badge on the main page highlightes the CI
status.

