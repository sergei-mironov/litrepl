## Other Development Scenatios

### Screencast Recording

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

### More Nix Targets

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
* `vim-demo` - Vim configured to use litrepl suitable for recording screencasts.
  Uses the latest released version of Litrepl rather than the current revision.
* `vim-plug` - Vim configured to use litrepl via the Plug manager
* `shell-dev` - The development shell
* `shell-screencast` - The shell for recording demonstrations, includes `vim-demo`.

See the `local.collection` attribute-set in the
[default.nix](../static/default.nix) for the full list of defined targets.

Note: The default development shell `shell-dev` installs many dependencies,
the users are encouraged to define their own shells when needed.


### More Development Scenarios

The top-level [Makefile](../static/Makefile) encodes common development scenarios:

<!--
``` python
print("~~~~ shell\n[ LitREPL-DEV ] $ make help")
!make help | grep -v -E 'Entering|Leaving'
print("~~~~")
```
-->
<!-- result -->
~~~~ shell
[ LitREPL-DEV ] $ make help
LitREPL is a macroprocessing Python library for Litrate programming and code execution
Build targets:
dist:         Build Python and Vim packages
docs:         Build the MkDocs documentation
examples:     Build examples
help:         Print help
man:          Build a manpage
paper-md:     Check and compile the paper PDF out of its Markdown source using JOSS tools
paper-quick:  Compile the paper PDF out of its LaTeX source without re-evaluation
paper:        Check and compile the paper PDF out of its LaTeX source
readme:       Update code sections in the README.md
test-small:   Run tests script using just the current Python and Shell interpreters
test:         Run tests script using all available interpreters
upload:       Upload Python wheel to Pypi.org (./_token.pypi is required)
version:      Print the version
vimbundle:    Build Vim bundle
wheel:        Build Python wheel (the DEFAULT target)
~~~~
<!-- noresult -->
