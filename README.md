LitREPL.vim
===========

**LitREPL** is a command-line tool and a Vim plugin for Python [literate
programming](https://en.wikipedia.org/wiki/Literate_programming), aimed at
providing the text-friendly code editing and execution workflow.


~~~~ markdown
Consider this Markdown document.

``` python
print("Hello, World!")
```

Having LitREPL tool and plugin installed, users get **:LitEval1**,
**:LitEvalAll** and alike Vim commands to run Python code sections right
in the editor.

``` result
Hello, World!
```

Any messages printed are pasted back into the corresponding result sections.
The execution takes place in a background interpreter, tied to the UNIX pipes
residing in the filesystem. Thus, the state of the interpreter is persistent
between the executions and in fact between the Vim editing sessions.
~~~~

<details><summary>Features</summary><p>

* Lightweight: Has only a few dependencies.
* Supported document formats: Markdown [[MD]](./doc/example.md), Latex
  [[TEX]](./doc/example.tex)[[PDF]](./doc/example.pdf).
* Supported interpreters: Python, IPython
* Supported editor: Vim

</p></details>

<details><summary>Requirements</summary><p>

* POSIX-compatible OS, typically a Linux. The plugin relies on POSIX pipes and
  depends on certain shell commands.
* More or less recent `Vim`
* Python3 with the following libraries: `lark-parser` (Required).
* Command line tools: `GNU socat` (Optional), `ipython` (Optional).

</p></details>

Contents
--------

<details><summary>Show</summary><p>
<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Usage](#usage)
  * [Text formatting](#text-formatting)
  * [Vim and Command line commands](#vim-and-command-line-commands)
  * [Vim variables and Command line arguments](#vim-variables-and-command-line-arguments)
* [Development](#development)
* [Gallery](#gallery)
* [Technical details](#technical-details)
* [Limitations](#limitations)
* [Related projects](#related-projects)
* [Third-party issues](#third-party-issues)

<!-- vim-markdown-toc -->
</p></details>

Installation
------------

To run the setup, one needs to install a Python package and a Vim plugin. The
Vim plugin relies on the `litrepl` script and on some third-party UNIX tools
available via the system `PATH`. We advise users to git-clone the same
repository with all the package managers involved to match the versions. Below
are the instructions for some packaging system combinations.

<details><summary>Pip and Plug</summary><p>

Instructions for the Pip and [Plug](https://github.com/junegunn/vim-plug)
manager of Vim:

1. Install the Python package.
   ```sh
   $ pip install --user git+https://github.com/grwlf/litrepl.vim
   $ litrepl --version
   ```
2. Install the Vim plugin by adding the following line between the
   `plug#begin` and `plug#end` lines of your `.vimrc` file:
   ```vim
   Plug 'https://github.com/grwlf/litrepl.vim' , { 'rtp': 'vim' }
   ```
</p></details>
<details><summary>Nix</summary><p>

Consider following the [Development guide](./doc/develop.md)

</p></details>

Usage
-----

### Text formatting

* [Formatting Markdown documents](./doc/formatting.md#markdown)
* [Formatting LaTeX documents](./doc/formatting.md#latex)

### Vim and Command line commands

| Vim             | Command line         | Description                          |
|-----------------|----------------------|--------------------------------------|
| `:LitStart`     | `litepl start`       | Start the interpreter     |
| `:LitStop`      | `litepl stop`        | Stop the interpreter      |
| `:LitStatus`    | `litepl status <F`     | Print the daemon status |
| `:LitEval1`     | `lirtepl --timeout-initial=0.5 --timeout-continue=0 eval-sections (N\|L:C) <F` | Run section under the cursor and wait a bit before going asynchronous. Also, update the output from the already running section. |
| `:LitEvalBreak1`| `lirtepl interrupt (N\|L:C) <F`       | Send Ctrl+C signal to the interpreter and get a feedback |
| `:LitEvalWait1` | `lirtepl eval-sections (N\|L:C) <F`   | Run or update section under the cursor and wait until the completion |
| `:LitEvalAbove` | `lirtepl eval-sections '0..(N\|L:C)' <F`| Run sections above and under the cursor and wait until the completion |
| `:LitEvalBelow` | `lirtepl eval-sections '(N\|L:C)..$' <F`| Run sections below and under the cursor and wait until the completion |
| `:LitEvalAll`   | `lirtepl eval-sections '0..$' <F`       | Evaluate all code sections |
|                 | `lirtepl eval-code <P`                  | Evaluate the given Python code |
| `:LitRestart`   | `litrepl restart`    | Restart the interpreter   |
| `:LitRepl`      | `lirtepl repl`       | Open the terminal to the interpreter |
| `:LitOpenErr`   | N/A                  | Open the stderr window    |
| `:LitVersion`   | `litrepl --version`  | Show version              |

Where

* `F` denotes the document
* `P` denotes the Python code
* `N` denotes the number of code section starting from 0.
* `L:C` denotes line:column of the cursor.

To evaluate the whole document:

```sh
$ cat doc/example.md | \
  litrepl --filetype=markdown --interpreter=ipython eval-sections 0..$
```

### Vim variables and Command line arguments


| Vim setting               | CLI argument         | Description                       |
|---------------------------|----------------------|-----------------------------------|
| `set filetype`            | `--filetype=T`       | Input file type: `latex`\|`markdown` |
| N/A                       | `--interpreter=I`    | The interpreter to use: `python`\|`ipython`\|`auto` (the default) |
| `let g:litrepl_debug=0/1` |  `--debug=1`         | Print debug messages to the stderr |
| `let g:litrepl_errfile="/tmp/litrepl.vim"` |  N/A  | Intermediary file for debug and error messages |
| `let g:litrepl_always_show_stderr=0/1`   |  N/A  | Set to auto-open stderr window after each execution |
| N/A                 |  `--timeout-initial=FLOAT` | Timeout to wait for the new executions, in seconds, defaults to inf |
| N/A                 |  `--timeout-continue=FLOAT`| Timeout to wait for executions which are already running, in seconds, defaults to inf |

* `I` is taken into account by the `start` command or by the first call to
  `eval-sections`.

The plugin does not define any Vim key bindings, users are expected to do it by
themselves, for example:

```vim
nnoremap <F5> :LitEval1<CR>
nnoremap <F6> :LitEvalBreak1<CR>
```

Development
-----------

See the [Development guide](./doc/develop.md)

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

Format conversion

* https://pandoc.org/

Documenting

* https://github.com/lervag/vimtex
* https://github.com/preservim/vim-markdown

Code execution

* https://www.ctan.org/pkg/pyluatex
* https://github.com/dccsillag/magma-nvim
* https://github.com/metakirby5/codi.vim
* https://github.com/gpoore/pythontex
* https://github.com/gpoore/pythontex
* https://github.com/gpoore/codebraid
* https://github.com/hanschen/vim-ipython-cell
* https://github.com/ivanov/vim-ipython
* https://github.com/goerz/jupytext.vim
  - https://github.com/mwouts/jupytext
* https://github.com/ivanov/ipython-vimception

Graphics

* https://github.com/sergei-grechanik/vim-terminal-images

Third-party issues
------------------

* https://github.com/junegunn/vim-plug/issues/1010#issuecomment-1221614232
* https://github.com/jgm/pandoc/issues/8598
* https://github.com/mwouts/jupytext/issues/220#issuecomment-1418209581


