LitREPL.vim
-----------

**LitREPL** is a VIM plugin and a macro processing Python library for Literate
programming and code execution right inside the editor.

<img src="./demo.gif" width="400"/>

**Features**

* Lightweight: Runs on a bare Python with the
  [lark-parser](https://github.com/lark-parser/lark) library
* Supported document formats: Markdown \[MD\], Latex
  [[TEX]](./data/example.tex)[[PDF]](./data/example.pdf)
* Supported interpreters: Python, IPython
* Supported editor: Vim
* Nix/NixOS - friendly

**Requirements:**

* POSIX-compatible OS, typically a Linux. The plugin depends on UNIX pipes and
  certain shell commands.
* More or less recent `Vim`
* Python3 with the following libraries: `lark-parser` (Required), `ipython`
  (Optional).
* (Optional) `GNU socat` application.

**Limitations:**

* Formatting: Nested code sections are not supported.
* Formatting: Special symbols in the Python output could invalidate the
  document.
* Interpreter: Extra newline is required after Python function definitions.
* Interpreter: Stdout and stderr are joined together.
* Interpreter: Evaluation of a code section locks the editor.
* Interpreter: Tweaking `os.ps1`/`os.ps2` prompts of the Python interpreter
  could break the session.
* Interpreter: No asynchronous code execution.
* ~~Interpreter: Background Python interpreter couldn't be interrupted~~

_Currently, the plugin is at the proof-of-concept stage. No code is packaged,
clone this repository to reproduce the results!_

Contents
--------

1. [LitREPL.vim](#litrepl.vim)
2. [Contents](#contents)
3. [Setup](#setup)
4. [Vim Commands](#vim-commands)
5. [Formatting](#formatting)
   * [Markdown](#markdown)
   * [Latex](#latex)
6. [Technical details](#technical-details)

Setup
-----

### [Plug](https://github.com/junegunn/vim-plug)

1. Add the following line to your `.vimrc` between `plug#begin` and `plug#end`
   calls.
   ```vim
   Plug 'https://github.com/grwlf/litrepl.vim' , { 'rtp': 'vim' }
   ```
2. Install `litrepl` python package. The plugin relies on the `litrepl` script
   to be available via system `PATH`.
   ```sh
   pip install litrepl
   ```

### Nix/NixOS

[default.nix](./default.nix) contains a `testvim` expression which may be
built with `nix-build -A testvim` and run with `./result/bin/testvim`. Modify
your system's configuration accordingly.

### Development environment

1. `git clone --recursive <https://this_repo>; cd litrepl.vim`
2. Enter the development environment
   * (Nix/NixOS systems) `nix-shell`
   * (Other Linuxes) `. env.sh`
   Read the warnings and install the missing packages if required. The
   environment script will add `./sh` and `./python` folders to the current
   shell's PATH.  The former folder contains the back-end script, the latter one
   contains the back-end script.
3. Run the `vim_litrepl_dev` (a thin wrapper around Vim) to run the Vim with the
   LitREPL plugin from the `./vim` folder.
4. (Optional) Run `test.sh`

Vim Commands
------------

* `:LitStart`/`:LitStop`/`:LitRestart` - Starts, stops or restarts the
  background Python interpreter
* `:LitEval1` - Execute the executable section under the cursor, or the
  executable section of the result section under the cursor
* `:LitRepl` - Open the `socat` with the right argument in the Vim terminal.
  This way users could inspect the state of Python interpreter which normally
  runs in the background. Note, that standard Python prompts `>>>`/`...` are
  disabled.

Formatting
----------

### Markdown

```` markdown
Executable section is the one that marked with "python" tag. Putting the cursor
on it and typing the :LitEval1 command would execute it in a background Python
interpreter.

```python
W='Hello, world!'
print(W)
```

Pure verbatim section next to the executable section is a result section. The
output of the code from the executable section will be pasted here. The original
content of the section will be replaced.

```
PlAcEhOlDeR
```

Markdown comments with `litrepl` word marks a special kind of result section for
verbatim results. This way we can generate parts of the markdown document.

<!--litrepl-->
PlAcEhOlDeR
<!--litrepl-->

````

### Latex

````latex
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}

LitREPL for latex recognizes specifically named environments as code and result
sections. It doesn't really evaluate Tex commands so renaming those environments
wouldn't work. But we still need to introduce it to Latex so we start with some
newenvironment declarations

\newenvironment{lcode}{\begin{texttt}}{\end{texttt}}
\newenvironment{lresult}{\begin{texttt}}{\end{texttt}}
\newcommand{\linline}[2]{#2}

Executable section is the one inside the \texttt{lcode} environment. Putting the
cursor on it and typing the \texttt{:LitEval1} command would execute it in a
background Python interpreter.

\begin{lcode}
W='Hello, world!'
print(W)
\end{lcode}

\texttt{lresult} section next to the executable section is a result section. The
output of the code from the executable section will be pasted here. The original
content of the section will be replaced.

\begin{lresult}
PlAcEhOlDeR
\end{lresult}

Commented \texttt{lresult} environmet is still recognized as an output section.
This way users can generate parts of the latex document.

\begin{lcode}
print("Hi")
\end{lcode}

%\begin{lresult}
PlAcEhOlDeR
%\end{lresult}

For LaTeX, VimREPL also recognises \texttt{linline} tag for which it prints its
first argument and pastes the result in place of the second argument.

\linline{W}{?}

\end{document}
````

Technical details
-----------------

The following events should normally happen upon typing the `LitEval1` command:

1. On the first run, the Python interpreter will be started in the
   background. Its standard input and output will be redirected into UNIX
   pipes in the current directory. Its PID will be saved into the
   `./_pid.txt` file.
2. The code from the Markdown code section under the cursor will be piped
   through the interpreter.
3. The result will be pasted into the Markdown section next after the current
   one.

Third-party issues
------------------

* https://github.com/junegunn/vim-plug/issues/1010#issuecomment-1221614232


