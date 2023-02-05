LitREPL.vim
-----------

**LitREPL** is a macro processing Python library and a Vim plugin for Literate
programming and code execution right from the editor.

<img src="https://github.com/grwlf/litrepl-media/blob/main/demo.gif?raw=true" width="400"/>

**Features**

* Lightweight: Runs on a system where only a few Python packages are installed.
* Supported document formats: Markdown [[MD]](https://raw.githubusercontent.com/grwlf/litrepl.vim/main/doc/example.md), Latex
  [[TEX]]()[[PDF]](./doc/example.pdf)
* Supported interpreters: Python, IPython
* Supported editor: Vim
* Nix/NixOS - friendly

**Requirements:**

* POSIX-compatible OS, typically a Linux. The plugin depends on UNIX pipes and
  certain shell commands.
* More or less recent `Vim`
* Python3 with the following libraries: `lark-parser`
  (Required), `setuptools_scm`, `ipython` (Optional).
* `GNU socat` application (Optional).

_The project is unstable, please install packages by cloning this repository!_

Contents
--------

 1. [LitREPL.vim](#litrepl.vim)
 2. [Contents](#contents)
 3. [Install](#install)
    * [Pip and Plug](#pip-and-plug)
    * [Nix](#nix)
 4. [Develop](#develop)
 5. [Usage](#usage)
    * [Basics](#basics)
    * [Commands](#commands)
    * [Arguments](#arguments)
    * [Batch processing](#batch-processing)
 6. [Formatting](#formatting)
    * [Markdown](#markdown)
      * [Syntax](#syntax)
      * [Converting to Jupyter Notebook](#converting-to-jupyter-notebook)
    * [Latex](#latex)
      * [Syntax](#syntax)
 7. [Gallery](#gallery)
 8. [Technical details](#technical-details)
 9. [Limitations](#limitations)
10. [Related projects](#related-projects)
11. [Third-party issues](#third-party-issues)


Install
-------

To run the setup, one needs to install a Python package and a Vim plugin. The
Vim plugin relies on the `litrepl` script and on some third-party UNIX tools
available via the system `PATH`. We advise users to git-clone the same
repository with all the package managers involved to match the versions. Below
are the instructions for some packaging system combinations.

### Pip and Plug

Instructions for the Pip and [Plug](https://github.com/junegunn/vim-plug)
manager of Vim:

1. Install the Python package.
   ```sh
   $ pip install lark setuptools-scm
   $ pip install git+https://github.com/grwlf/litrepl.vim
   $ litrepl --version
   ```
2. Install the Vim plugin by adding the following line between the
   `plug#begin` and `plug#end` lines of your `.vimrc` file:
   ```vim
   Plug 'https://github.com/grwlf/litrepl.vim' , { 'rtp': 'vim' }
   ```

### Nix

[default.nix](./default.nix) contains a set of Nix exressions. Expressions
prefixed with `shell-` are to be opened with `nix-shell -A NAME`. Other
expressions need to be built with `nix-build -A NAME` and run with
`./result/bin/...`. Some expressions are:

* `litrepl` - Litrepl script and Python lib
* `vim-litrepl` - Litrepl vim plugin
* `vim-test` - a minimalistic vim with a single litrepl plugin
* `vim-demo` - vim for recording screencasts
* `vim-plug` - vim configured to use the Plug manager
* `shell-demo` - shell for recording screencasts
* `shell` - Full development shell

Develop
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

A useful keymapping to reload the plugin:

```vim
nnoremap <F9> :unlet g:litrepl_bin<CR>:unlet g:litrepl_loaded<CR>:runtime plugin/litrepl.vim<CR>
```

To view debug messages, set

```vim
let g:litrepl_debug = 1
let g:litrepl_always_show_stderr = 1
```

Usage
-----

### Basics

LitREPL processes text documents written in the [literate
programming](https://en.wikipedia.org/wiki/Literate_programming) style combined
with the style of [Jupyter Notebooks](https://jupyter.org/). The text separates
code citation blocks followed by the result blocks followed by more text and
so on:

````{.markdown}
Some text text

<!-- Code block 1 -->
```python
print("Hello, World!")
```

More text text

<!-- Result block 1 -->
```lresult
Hello, World!
```

More text text
````

Vim command `:LitEval1` executes the code block under the cursor and pastes the
result into the corresponding result section. The execution takes place in the
background interpreter which is tied to the UNIX pipes saved in the filesystem.
Thus, the state of the interpreter is persistent between the executions and in
fact even between the Vim editing sessions.

There are no key bindings defined in the plugin, users are to define their own:

```vim
nnoremap <F5> :LitEval1<CR>
nnoremap <F6> :LitEvalBreak1<CR>
```

### Commands

Most of the commands could be sent from the command line or from Vim directly.

| Vim             | Command line         | Description                          |
|-----------------|----------------------|--------------------------------------|
| `:LitEval1`     | `lirtepl --timeout-initial=0.5 --timeout-continue=0 eval-sections (N\|L:C)` | Run section under the cursor and wait a bit before going asynchronous. Also, update the output from the already running section. |
| `:LitEvalBreak1`| `lirtepl interrupt (N\|L:C)`       | Send Ctrl+C signal to the interpreter and get a feedback |
| `:LitEvalWait1` | `lirtepl eval-sections (N\|L:C)`   | Run or update section under the cursor and wait until the completion |
| `:LitEvalAbove` | `lirtepl eval-sections 0..(N\|L:C)`| Run sections above and under the cursor and wait until the completion |
| `:LitEvalBelow` | `lirtepl eval-sections (N\|L:C)..$`| Run sections below and under the cursor and wait until the completion |
| `:LitRepl`      | `lirtepl repl`       | Open the terminal to the interpreter |
| `:LitStart`     | `litepl start`       | Start the interpreter     |
| `:LitStop`      | `litepl stop`        | Stop the interpreter      |
| `:LitRestart`   | `litrepl restart`    | Restart the interpreter   |
| `:LitOpenErr`   | N/A                  | Open the stderr window    |
| `:LitVersion`   | `litrepl --version`  | Show version              |

Where

* `N` denotes the number of code section starting from 0.
* `L:C` denotes line:column of the cursor.

### Arguments

| Vim setting               | CLI argument         | Description                       |
|---------------------------|----------------------|-----------------------------------|
| `set filetype`            | `--filetype=T`       | Input file type: `latex`\|`markdown`  |
| N/A                       | `--interpreter=I`    | The interpreter to use: `python`\|`ipython`\|`auto`, defaulting to `auto` |
| `let g:litrepl_debug=0/1` |  `--debug=1`         | Print debug messages to the stderr |
| `let g:litrepl_errfile="/tmp/litrepl.vim"` |  N/A  | Intermediary file for debug and error messages |
| `let g:litrepl_always_show_stderr=0/1`   |  N/A  | Set to auto-open stderr window after each execution |
| N/A                 |  `--timeout-initial=FLOAT` | Timeout to wait for the new executions, in seconds, defaults to inf |
| N/A                 |  `--timeout-continue=FLOAT`| Timeout to wait for executions which are already running, in seconds, defaults to inf |

* `I` is taken into account by the `start` command and by the first
  `eval-sections` only.

### Batch processing

To evaluate the document run the following command

```sh
$ cat doc/example.md | \
  litrepl --filetype=markdown --interpreter=ipython eval-sections 0..$
```

Formatting
----------

### Markdown

#### Syntax

````{.markdown}
Executable sections are marked with either "python", "lpython" or "code" tags.
Putting the cursor on one of the typing the :LitEval1 command executes its code
in a background Python interpreter.

``` python
W='Hello, World!'
print(W)
```

Verbatim sections with "result" or "lresult" tags are the result sections . The
output of the code from the executable section is pasted there. The original
content of the section is replaced with the output of the last execution.

``` result
Hello, World!
```

Markdown comments taged with `code`/`nocode`/`result`/`noresult` also mark
executable and result sections. This way we could hide the executable code from
Markdown renderers and generate the markup they recognize.
markup.

<!-- code
print("Hello, LitREPL")
-->

<!-- result -->
Hello, LitREPL
<!-- noresult -->

<!-- result
Hello, LitREPL
-->
````

#### Converting to Jupyter Notebook

[Pandoc](https://pandoc.org) could be used to conver LitREPL-frinedly markdown
documents to the Jupyter Notebook format. In order make it recognize code and
result fields addtional efforts are required. Currently we aware of two options:
1. Mark Jupyter sections with fenced-div markup as described in the [Pandoc
   manual](https://pandoc.org/MANUAL.html#jupyter-notebooks)
   1. Consider the following Markdown `file.md`
      ````{.markdown}
      :::::: {.cell .code execution_count=1}
      ```python
      print("hello XXXXXXX")
      ```
      ::: {.output .stream .stdout}
      ```lresult
      hello XXXXXXX
      ```
      :::
      ::::::
      ````
   2. It is recognized by both `LitREPL` and `Pandoc`, so to convert it to the
      Jupyter Notebook format one may run
      ```sh
      $ pandoc file.md -o file.ipynb
      ```
   3. Unfortunately, other renderers may interpret fenced divs directly,
      bloating the output.

2. Alternatively, native divs could be used.
   1. Consider the following Markdown `file.md`
      ````{.markdown}
      <div class="cell code">
      ```python
      print("hello markdown")
      ```

      <div class="output stream stdout">
      ```lresult
      hello markdown
      ```
      </div>
      </div>
      ````
   2. Again, both `LitREPL` and `Pandoc` would recognize the format, plus most
      third-party renderers would ignore `div` tags. To convert this file to the
      Jupyter Notebook format, call pandoc with
      [native divs extension](https://pandoc.org/MANUAL.html#extension-native_divs)
      enabled
      ```sh
      $ pandoc -f markdown+native_divs test.md -o test.ipynb
      ```

### Latex

#### Syntax

````latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

LitREPL for latex recognizes \texttt{lcode} environments as code and
\texttt{lresult} as result sections. The tag names is currently hardcoded into
the simple parser the tool is using, so we need to additionally introduce it to
the Latex system. Here we do it in a most simple way.

\newenvironment{lcode}{\begin{texttt}}{\end{texttt}}
\newenvironment{lresult}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

Executable section is the text between the \texttt{lcode} begin/end tags.
Putting the cursor on it and typing the \texttt{:LitEval1} executes it in the
background Python interpreter.

\begin{lcode}
W='Hello, World!'
print(W)
\end{lcode}

\texttt{lresult} tags next to the executable section mark the result section.
The output of the executable section will be pasted here. The
original content of the section will be replaced.

\begin{lresult}
Hello, World!
\end{lresult}

Commented \texttt{lresult}/\texttt{lnoresult} tags also marks result sections.
This way we could customise the Latex markup for every particular section.

\begin{lcode}
print("Hi!")
\end{lcode}

%lresult
Hi!
%lnoresult

Additionally, VimREPL for Latex recognises \texttt{linline} tags for which it
prints its first argument and pastes the result in place of the second argument.

\linline{W}{Hello, World!}

\end{document}
````

Gallery
-------

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
   directory. The PID is saved into the `./_pid.txt` file.
2. LitREPL runs the whole document through the express Markdown/Latex parser
   which determines the start/stop positions of code and result sections. Cursor
   position is also resolved and the code from the right code section goes to
   the interpreter.
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


