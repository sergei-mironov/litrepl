LitREPL
=======

**LitREPL** is a command-line text processing tool for code evaluation
aimed at enabling
[literate programming](https://en.wikipedia.org/wiki/Literate_programming)
experience in common editors.

![2024-02-24 02-29-19](https://github.com/grwlf/litrepl.vim/assets/4477729/73fd31f6-2b2a-4193-b63e-5c163272a9d8)

Features
--------

* **Document formats** <br/>
  Markdown _(Example [[MD]](./doc/example.md))_ **|** [LaTeX](https://www.latex-project.org/) _(Examples [[TEX]](./doc/example.tex)[[PDF]](./doc/example.pdf))_
* **Interpreters** <br/>
  [Python](https://www.python.org/) **|** [IPython](https://ipython.org/) **|** [GPT4All-cli](https://github.com/sergei-mironov/gpt4all-cli)
* **Editor integration** <br/>
  Vim _(plugin included)_

<details><summary><h2>Requirements</h2></summary><p>

* POSIX-compatible OS, typically a Linux. The tool relies on POSIX pipes and
  depends on certain shell commands.
* More or less recent `Vim`
* Python3 with the following libraries: `lark-parser` (Required).
* Command line tools: `GNU socat` (Optional)

</p></details>

Contents
--------

<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Usage](#usage)
    * [Quick start](#quick-start)
    * [Reference](#reference)
        * [Vim and command-line commands](#vim-and-command-line-commands)
        * [Variables and arguments](#variables-and-arguments)
    * [Hints](#hints)
        * [Command line, basic usage](#command-line-basic-usage)
        * [Command line, foreground evaluation](#command-line-foreground-evaluation)
        * [Vim, adding keybindings](#vim-adding-keybindings)
        * [Vim, inserting new sections](#vim-inserting-new-sections)
        * [Vim, executing first section after restart](#vim-executing-first-section-after-restart)
        * [Vim, running shell commands](#vim-running-shell-commands)
* [Development](#development)
    * [Development shells](#development-shells)
    * [Other Nix targets](#other-nix-targets)
    * [Common workflows](#common-workflows)
* [Gallery](#gallery)
* [Technical details](#technical-details)
* [Limitations](#limitations)
* [Related projects](#related-projects)
* [Third-party issues](#third-party-issues)

<!-- vim-markdown-toc -->

Installation
------------

The repository includes a Python tool and an interface Vim plugin. The Python
part should be installed with `pip install` as usual. The Vim part requires
plugin manager like `Plug` or hand-copying files to a .vim config folder.

The generic installation procedure:

<details><summary><b>pip-install and Vim-Plug</b></summary><p>

Instructions for the [Pip](https://pypi.org) and [Vim-plug](https://github.com/junegunn/vim-plug):

1. Install the `litrepl` Python package with pip:
   ```sh
   $ pip install --user git+https://github.com/grwlf/litrepl.vim
   $ litrepl --version
   ```
2. Install the Vim plugin by adding the following line between the
   `plug#begin` and `plug#end` lines of your `.vimrc` file:
   ```vim
   Plug 'https://github.com/grwlf/litrepl.vim' , { 'rtp': 'vim' }
   ```
   Note: `rtp` sets the custom vim-plugin source directory of the plugin.

</p></details>

<details><summary><b>Nix and vim_configurable</b></summary><p>

Nix/NixOS users can follow the formalized path:

Nix supports
[configurable Vim expressions](https://nixos.wiki/wiki/Vim#System_wide_vim.2Fnvim_configuration).
To enable the Litrepl plugin, just add the `vim-litrepl.vim-litrepl-release` to the
list of Vim packages.

``` nix
let
  vim-litrepl = import <path/to/litrepl.vim> {};
in
vim_configurable.customize {
  name = "vim";
  vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
    start = [
      ...
      vim-litrepl.vim-litrepl-release
      ...
    ];
  };
}
```

Note: `vim-demo` expression from the [default.nix](./default.nix) provides
an example Vim configuration. Use `nix build '.#vim-demo'` to build it and then
`./result/bin/vim-demo` to run the editor.

See the [Development](#development) section for more details.

</p></details>

Usage
-----

### Quick start

Create separate 'python' and 'result' sections within your Markdown or LaTeX
document. Insert Python code into the 'python' section, then use the ':LEval'
command to execute that section at the cursor location.

   ~~~~
   Markdown                             Latex
   --------                             -----

   ``` python                           \begin{lcode}
   print('Hello Markdown!')             print('Hello LaTeX!')
   ```                                  \end{lcode}


   ``` result                           \begin{lresult}
   Hello Markdown!                      Hello LaTeX!
   ```                                  \end{lresult}
   ~~~~


See also:
- [Formatting Markdown documents](./doc/formatting.md#markdown)
- [Formatting LaTeX documents](./doc/formatting.md#latex)


### Reference

#### Vim and command-line commands

| Vim <img width=200/> | Command line <img width=200/> | Description                 |
|----------------------|----------------------|--------------------------------------|
| `:LStart`            | `litrepl start`      | Start the interpreter                |
| `:LStop`             | `litrepl stop`       | Stop the interpreter                 |
| `:LStatus`           | `litrepl status <F`  | Print the daemon status              |
| `:LRestart`          | `litrepl restart`    | Restart the interpreter              |
| `:LEval N`           | `lirtepl eval-sections N <F`     | Run or update section under the cursor and wait until the completion |
| `:LEvalAbove N`      | `lirtepl eval-sections '0..N' <F`| Run sections above and under the cursor and wait until the completion |
| `:LEvalBelow N`      | `lirtepl eval-sections 'N..$' <F`| Run sections below and under the cursor and wait until the completion |
| `:LEvalAll`          | `lirtepl eval-sections <F`       | Evaluate all code sections |
| `:LEvalAsync N`      | `lirtepl --timeout=0.5,0 eval-sections N <F` | Run section under the cursor and wait a bit before going asynchronous. Also, update the output from the already running section. |
| `:LInterrupt N`      | `lirtepl interrupt N <F`         | Send Ctrl+C signal to the interpreter and get a feedback |
| `:LMon`              | `while .. do .. done`            | Monitor asynchronous code evaluation |
| N/A                  | `lirtepl eval-code <P`           | Evaluate the given Python code |
| `:LTerm`             | `lirtepl repl`       | Open the terminal to the interpreter |
| `:LOpenErr`          | `litrepl ...  2>F`   | Open the stderr window               |
| `:LVersion`          | `litrepl --version`  | Show version                         |

Where

* `F` denotes the document
* `P` denotes the Python code
* `N` denotes the number of code section starting from 0.
* `L:C` denotes line:column of the cursor.


#### Variables and arguments

| Vim setting                     | CLI argument           | Description                       |
|---------------------------------|------------------------|-----------------------------------|
| `set filetype`                  | `--filetype=T`         | Input file type: `latex`\|`markdown` |
| `let g:litrepl_interpreter=EXE` | `--interpreter=I`      | The interpreter to use: `python`\|`ipython`\|`auto` (the default) |
| `let g:litrepl_debug=0/1`       | `--debug=1`            | Print debug messages to the stderr |
| `let g:litrepl_errfile=FILE`    | N/A                    | Intermediary file for debug and error messages |
| `let g:litrepl_always_show_stderr=0/1` |  N/A            | Set to auto-open stderr window after each execution |
| `let g:litrepl_timeout=FLOAT`   | `--timeout=FLOAT`      | Timeout to wait for the new executions, in seconds, defaults to inf |

* `I` is taken into account by the `start` command or by the first call to
  `eval-sections`.

### Hints

#### Command line, basic usage

To evaluate code section in a document:

```sh
$ cat doc/example.md | litrepl --interpreter=ipython eval-sections >output.md
```

To evaluate a Python script:

```sh
$ cat script.py | litrepl --interpreter=ipython eval-code
```

Note that both commands above share the same background interpreter session.


#### Command line, foreground evaluation

For batch processing of documents, it may be necessary to have an on-demand
interpreter session available, which would exist solely for the duration of the
evaluation process.

~~~~ sh
$ cat >document.md.in <<EOF
``` python
raise Exception("D'oh!")
```
EOF
$ cat document.md.in | litrepl --foreground --exception-exit=200 eval-sections >document.md
$ echo $?
200
~~~~

Here, the `--foreground` argument tells Litrepl to run a new interpreter session
and then stop it before exiting, `--exception-exit=200` sets the exit code
returned in the case of unhandled exceptions.

#### Vim, adding keybindings

The plugin does not define any keybindings, but users could do it by themselves,
for example:

``` vim
nnoremap <F5> :LEval<CR>
nnoremap <F6> :LEvalAsync<CR>
```

#### Vim, inserting new sections

Below we define `:C` command inserting new sections.

``` vim
command! -buffer -nargs=0 C normal 0i``` python<CR>```<CR><CR>``` result<CR>```<Esc>4k
```

#### Vim, executing first section after restart

We define the `:LR` command running first section after the restart.

``` vim
command! -nargs=0 LR LRestart | LEval 0
```

#### Vim, running shell commands

Thanks to IPython features, we can use exclamation to run shell commands
directly from Python code sections.

~~~~
``` python
!cowsay "Hello, Litrepl!"
```

``` result
 _________________
< Hello, Litrepl! >
 -----------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```
~~~~

Development
-----------

This project uses [Nix](https://nixos.org/nix) as a primary development
framework. [flake.nix](./flake.nix) handles the source-level Nix dependencies
while the [default.nix](./default.nix) defines the common build targets
including Pypi and Vim packages, demo Vim configurations, development shells,
etc.

### Development shells

The default development shell is defined in the `./default.nix` as a Nix
expression named `shell` which is the default name for development shells.
Running

``` sh
$ nix develop
```

will ask Nix to install the development dependencies and open the shell.

### Other Nix targets

Another shell which might be useful is `shell-screencast`. This would build the
full set of Litrepl tools and makes sure that the screencasting software is
available. To enter it, specify its Nix-flake path as follows:

``` sh
$ nix develop '.#shell-screencast'
```

To build individual Nix expressions, run `nix build '.#NAME'` passing the
name of Nix-expression to build. If succeeded, Nix publishes the last build'
results under the `./result` symlink.

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

See Nix flakes manual for other Nix-related details.

### Common workflows

The top-level [Makefile](./Makefile) encodes common development workflows:

``` sh
[LitREPL-develop] $ make help
LitREPL is a macroprocessing Python library for Litrate programming and code execution
Build targets:
help:       Print help
test:       Run the test script (./sh/test.sh)
wheel:      Build Python wheel (the DEFAULT target)
version:    Print the version
upload:     Upload wheel to Pypi.org (./_token.pypi is required)
```

Gallery
-------

Basic usage

<img src="https://github.com/grwlf/litrepl-media/blob/main/demo.gif?raw=true" width="400"/>

Using LitREPL in combination with the [Vimtex](https://github.com/lervag/vimtex)
plugin to edit Latex documents on the fly.


<video controls src="https://user-images.githubusercontent.com/4477729/187065835-3302e93e-6fec-48a0-841d-97986636a347.mp4" muted="true"></video>

Asynchronous code execution

<img src="https://user-images.githubusercontent.com/4477729/190009000-7652d544-a668-4440-933d-799f3410736f.gif" width="510"/>


Technical details
-----------------

The following events should normally happen after users type the `:LitEval1`
command:

1. On the first run, LitREPL starts the Python interpreter in the background.
   Its standard input and output are redirected into UNIX pipes in the current
   directory.
2. LitREPL runs the whole document through the express Markdown/Latex parser
   determining the start/stop positions of code and result sections. The cursor
   position is also available and the code from the right code section can
   reach the interpreter.
3. The process which reads the interpreter's response is forked out of the main
   LitREPL process. The output goes to the temporary file.
4. If the interpreter reports the completion quickly, the output is pasted to
   the resulting document immediately. Otherwise, the temporary results are
   pasted.
5. Re-evaluating sections with temporary results causes LitREPL to update
   these results.

Limitations
-----------

* Formatting: Nested code sections are not supported.
* Formatting: Special symbols in the Python output could invalidate the
  document.
* Interpreter: Extra newline is required after Python function definitions.
* Interpreter: Stdout and stderr are joined together.
* Interpreter: Evaluation of a code section locks the editor.
* Interpreter: Tweaking `os.ps1`/`os.ps2` prompts of the Python interpreter
  could break the session.
* ~~Interpreter: No asynchronous code execution.~~
* ~~Interpreter: Background Python interpreter couldn't be interrupted~~

Related projects
----------------

Edititng:

* https://github.com/lervag/vimtex (LaTeX editing, LaTeX preview)
* https://github.com/shime/vim-livedown (Markdown preview)
* https://github.com/preservim/vim-markdown (Markdown editing)

Code execution:

* Vim-medieval https://github.com/gpanders/vim-medieval
  - Evaluates Markdown code sections
* Pyluatex https://www.ctan.org/pkg/pyluatex
* Magma-nvim https://github.com/dccsillag/magma-nvim
* Codi https://github.com/metakirby5/codi.vim
* Pythontex https://github.com/gpoore/pythontex
  - Evaluates Latex code sections
* Codebraid https://github.com/gpoore/codebraid
* Vim-ipython-cell https://github.com/hanschen/vim-ipython-cell
* Vim-ipython https://github.com/ivanov/vim-ipython
* Jupytext https://github.com/goerz/jupytext.vim
  - Alternative? https://github.com/mwouts/jupytext
* Ipython-vimception https://github.com/ivanov/ipython-vimception

Useful Vim plugins:

* https://github.com/sergei-grechanik/vim-terminal-images (Graphics in vim terminals)

Useful tools:

* https://pandoc.org/

Third-party issues
------------------

* Vim-plug https://github.com/junegunn/vim-plug/issues/1010#issuecomment-1221614232
* Pandoc https://github.com/jgm/pandoc/issues/8598
* Jupytext https://github.com/mwouts/jupytext/issues/220#issuecomment-1418209581
* Vim-LSC https://github.com/natebosch/vim-lsc/issues/469


