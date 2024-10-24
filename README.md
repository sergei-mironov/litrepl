LitREPL
=======

**LitREPL** is a command-line tool that brings together the benefits of
[literate programming](https://en.wikipedia.org/wiki/Literate_programming) and
[read-eval-print-loop coding](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop).
LitREPL comes bundled with an interface Vim plugin, integrating it into the editor.

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)


Features
--------

* **Document formats** <br/>
  Markdown _(Example [[MD]](./doc/example.md))_ **|** [LaTeX](https://www.latex-project.org/) _(Examples [[TEX]](./doc/example.tex)[[PDF]](./doc/example.pdf))_
* **Interpreters** <br/>
  [Python](https://www.python.org/) **|** [IPython](https://ipython.org/) **|** [Aicli](https://github.com/sergei-mironov/aicli)
* **Editor integration** <br/>
  Vim _(plugin included)_

<details><summary><h2>Requirements</h2></summary><p>

* POSIX-compatible OS, typically a Linux. The tool relies on POSIX pipes and
  depends on certain shell commands.
* Python packages: `lark-parser`, `psutil` (Required).
* Command line tools: `GNU socat` (Optional)

</p></details>

Contents
--------

<!-- vim-markdown-toc GFM -->

* [Installation](#installation)
* [Usage](#usage)
    * [Overview](#overview)
        * [Basic evaluation](#basic-evaluation)
        * [Managing sessions](#managing-sessions)
        * [Asynchronous execution](#asynchronous-execution)
        * [Examining internal state](#examining-internal-state)
        * [Communicating with AI (Experimental)](#communicating-with-ai-experimental)
    * [Reference](#reference)
        * [Vim and command-line commands overview](#vim-and-command-line-commands-overview)
        * [Variables and arguments overview](#variables-and-arguments-overview)
        * [Command-line arguments](#command-line-arguments)
    * [Applications](#applications)
        * [Command line, basic usage](#command-line-basic-usage)
        * [Command line, foreground evaluation](#command-line-foreground-evaluation)
        * [GNU Make, updating documentation](#gnu-make-updating-documentation)
        * [Vim, adding keybindings](#vim-adding-keybindings)
        * [Vim, inserting new sections](#vim-inserting-new-sections)
        * [Vim, executing first section after restart](#vim-executing-first-section-after-restart)
        * [Vim, running shell commands](#vim-running-shell-commands)
        * [Vim, executing text selection](#vim-executing-text-selection)
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

This repository includes the Litrepl tool in Python and an interface Vim plugin.
The Python part might be installed with `pip install .` run from the project
folder. The Vim part requires hand-copying `./vim/plugin/litrepl.vim` to the
`~/.vim` config folder or using any Vim plugin manager, e.g. Vim-Plug.

<details><summary><b>Release versions from pypi and vim.org</b></summary><p>

1. `pip install litrepl`
2. Download the `litrepl.vim` from the vim.org
   [script page](https://www.vim.org/scripts/script.php?script_id=6117) and put it into
   your `~/.vim/plugin` folder.

</p></details>

<details><summary><b>Latest versions using pip-install and Vim-Plug</b></summary><p>

1. Install the `litrepl` Python package with pip:
   ```sh
   $ pip install --user git+https://github.com/sergei-mironov/litrepl
   $ litrepl --version
   ```
2. Install the Vim plugin by adding the following line between the
   `plug#begin` and `plug#end` lines of your `.vimrc` file:
   ```vim
   Plug 'https://github.com/sergei-mironov/litrepl' , { 'rtp': 'vim' }
   ```
   Note: `rtp` sets the custom vim-plugin source directory of the plugin.

</p></details>

<details><summary><b>Development environment using Nix</b></summary><p>

The repository also includes a set of Nix expressions that automate installation
on Nix-enabled systems.

Nix supports
[configurable Vim expressions](https://nixos.wiki/wiki/Vim#System_wide_vim.2Fnvim_configuration).
To enable the Litrepl plugin, add the `vim-litrepl.vim-litrepl-release` to the
list of Vim plugins and put this version of vim into your Nix profile. Litrepl
and its dependencies will be installed automatically.

``` nix
{ litrepl }:
...
vim_configurable.customize {
  name = "vim";
  vimrcConfig.packages.myVimPackage = with pkgs.vimPlugins; {
    start = [
      ...
      litrepl.vim-litrepl-release
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

### Overview

The tool sends verbatim sections from a document to external interpreters,
receiving the evaluated results in return. Litrepl currently supports two
flavors of Python and the Aicli interpreter.

#### Basic evaluation

Litrepl recognises verbatim code sections followed by zero or more result
sections. In Markdown documents, the code is any triple-quoted section labeled
as `python`. The result is any triple-quoted `result` section. In LaTeX
documents, sections are marked with `\begin{python}\end{python}` and
`\begin{result}\end{result}` environments correspondingly.

`litrepl eval-sections` is the main command evaluating the formatted document.
To run the evaluation, send the file to the input of the shell command.

For example:

<!--lignore-->
~~~~ shell
$ cat file.md
``` python
print('Hello Markdown!')
```

``` result
```
$ cat file.md | litrepl eval-sections
~~~~
<!--lnoignore-->

.. would produce a Markdown document containing the properly filled result
section.

~~~~ markdown
``` python
print('Hello Markdown!')
```

``` result
Hello Markdown!
```
~~~~

Below we also show what the relevant LaTeX part would look like:

~~~~ tex
\begin{python}
print('Hello LaTeX!')
\end{python}


\begin{result}
Hello LaTeX!
\end{result}
~~~~

* The equivalent Vim command is `:LEval`.`:LEval` accepts optional argument
  denoting the range: `all`, `above` (the cursor), `below` (the cursor), section
  number, etc.
* Litrepl expects Markdown formatting by default. Add `--filetype=tex` for Tex
  documents. Vim plugin does this automatically based on the `filetype`
  variable.
* Both command-line and Vim versions of the command accept code section indices.
  Everything is evaluated by default.
* LaTeX documents need a preamble introducing python/result tags to the Tex
  processor.  For details, see:
  - [Formatting LaTeX documents](./doc/formatting.md#latex)
* For more information on Markdown formatting, see
  - [Formatting Markdown documents](./doc/formatting.md#markdown)

#### Managing sessions

`litrepl start`, `litrepl stop` and `litrepl restart` manage the interpreter
sessions. The commands also accepts the type of the interpreter to operation on.
IPython interpreter is assumed by default.

`litrepl status` queries the information about the interpreters running in
the background. The command reveals the process PID and the command-line arguments.


``` shell
$ litrepl status
# Format:
# TYP  PID      EXITCODE  CMD
python 3900919  -         python3 -m IPython --config=/tmp/litrepl_1000_a2732d/python/litrepl_ipython_config.py --colors=NoColor -i
ai     3904696  -         aicli --readline-prompt=
```

* The interpreters are associates with the directory they were started in.
* The corresponding Vim commands are `:LStart`, `:LStop`, `:LRestart` and
  `:LStatus`


#### Asynchronous execution

Litrepl can produce output document earlier than the interpreter reports the
completion. In cases where the evaluation takes longer to finish, LitREPL will
leave a marker that allows it to pick up where it left off on subsequent
executions.

`litrepl --timeout=3.5 eval-sections` changes the reading timeout from the
default infinity the specified number of seconds. The output would be:

<!--lignore-->
~~~~ markdown
``` python
from tqdm import tqdm
from time import sleep
for i in tqdm(range(10)):
  sleep(1)
```

``` result
 30%|███       | 3/10 [00:03<00:07,  1.00s/it]
[BG:/tmp/nix-shell.vijcH0/litrepl_1000_a2732d/python/litrepl_eval_5503542553591491252.txt]
```
~~~~
<!--lnoignore-->

When re-executing this document, LitREPL will resume the reading. Once the
evaluation is complete, it will remove the continuation marker from the output
section.

`litrepl interrupt` will send interrupt signal to the interpreter so it return
the control earlier (with an exception).

* The corresponding Vim commands are `:LEvalAsyn` (with the timeout set to 0.5
  seconds by default) and `:LInterrupt`.
* Vim plugin defines `:LEvalMon` command that enables repeated code evaluation
  without any delay. Interrupting this process using Ctrl+C will cause Litrepl
  to return control to the editor while leaving the evaluation in the
  background.

#### Examining internal state

`litrepl repl` "manually" attaches to the interpreter session allowing us to
examine its internal state:

``` shell
$ litrepl repl
Opening the interpreter terminal (NO PROMPTS, USE `Ctrl+D` TO DETACH)
W = 'Hello from repl'
^D
```

* Python prompts are disabled internally, no `>>>` symbols are going to appear.
* The corresponding Vim command is `:LTerm`

`litrepl eval-code` might be used to pipe the code through the interpreter. The
`W` variable now resides in memory so we can query it as we would do in a
regular IPython session.

``` shell
$ echo 'W' | litrepl eval-code
'Hello from repl'
```

#### Communicating with AI (Experimental)

Litrepl experimentally supports
[Aicli](https://github.com/sergei-mironov/aicli) allowing users to
query local LLMs. In order to try it, install the interpreter and use `ai` as
the name for code sections. For low-speed models it would be convenient to use
`:LEvalMon` command for evaluation.

<!--lignore-->
~~~~ markdown
``` ai
/model "~/.local/share/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
Hi chat! What is your name?
```

``` result
I'm LLaMA, a large language model trained by Meta AI. I'm here to help answer
any questions you might have and provide information on a wide range of topics.
How can I assist you today?
```
~~~~
<!--lnoignore-->

For AI sections, Litrepl can paste text from other sections of the document in place of reference
markers. The markers have the following format:

* `>>RX<<`, where `X` is a number - references a section number `X` (starting from zero).
* `^^RX^^`, where `X` is a number - references the section `X` times above the current one.
* `vvRXvv`, where `X` is a number - references the section `X` times below the current one.

<!--lignore-->
~~~~ markdown
``` ai
AI, what do you think the following text means?

^^R1^^
```

``` result
Another interesting piece of text!
This is an example of a chatbot introduction or "hello message." It appears to
be written in a friendly, approachable tone, with the goal of establishing a
connection with users.
```
~~~~
<!--lnoignore-->

### Reference

#### Vim and command-line commands overview

| Vim <img width=200/> | Command line <img width=200/>    | Description                 |
|----------------------|----------------------------------|-----------------------------|
| `:LStart [T]`        | `litrepl start [T]`              | Start the background interpreter |
| `:LStop [T]`         | `litrepl stop [T]`               | Stop the background interpreter |
| `:LRestart [T]`      | `litrepl restart [T]`            | Restart the background interpreter |
| `:LStatus [T]`       | `litrepl status [T] <F`          | Print the background interpreter status |
| `:LEval [N]`         | `lirtepl eval-sections L:C <F`   | Evaluate the section under the cursor synchronously |
| `:LEval above`       | `lirtepl eval-sections '0..N' <F`| Evaluate sections above and under the cursor synchronously |
| `:LEval below`       | `lirtepl eval-sections 'N..$' <F`| Evaluate sections below and under the cursor synchronously |
| `:LEval all`         | `lirtepl eval-sections <F`       | Evaluate all code sections in a document |
| `:LEvalAsync N`      | `lirtepl --timeout=0.5,0 eval-sections N <F` | Start or continue asynchronous evaluation of the section under the cursor |
| `:LInterrupt N`      | `lirtepl interrupt N <F`         | Send SIGINT to the interpreter evaluating the section under the cursor and update |
| `:LEvalMon N`        | `while .. do .. done`            | Start or continue monitoring asynchronous code evaluation |
| N/A                  | `lirtepl eval-code <P`           | Evaluate the given code verbatim |
| `:LTerm`             | `lirtepl repl [T]`               | Connect to the interpreter using GNU socat |
| `:LOpenErr`          | `litrepl ...  2>F`               | Get the errors |
| `:LVersion`          | `litrepl --version`              | Show version |

Where

* `T` type of the interpreter: `python` or `ai` (some commands also accept `all`)
* `F` Path to a Markdown or LaTeX file
* `P` Path to a Python script
* `N` number of code section to evaluate, starting from 0.
* `L:C` denotes line:column of the cursor.

#### Variables and arguments overview

| Vim setting  <img width=200/>   | CLI argument  <img width=200/> | Description                       |
|---------------------------------|--------------------------------|-----------------------------------|
| `set filetype`                  | `--filetype=D`                 | Input file type: `latex`\|`markdown` |
| `let g:litrepl_python_interpreter=B` | `--python-interpreter=B`  | The Python interpreter to use: `python`\|`ipython`\|`auto` (the default) |
| `let g:litrepl_ai_interpreter=B`     | `--ai-interpreter=B`      | The AI interpreter to use: `aicli`\|`auto` (the default) |
| `let g:litrepl_debug=0/1`       | `--debug=0/1`                  | Print debug messages to the stderr |
| `let g:litrepl_timeout=FLOAT`   | `--timeout=FLOAT`              | Timeout to wait for the new executions, in seconds, defaults to inf |

* `D` type of the document: `tex` or `markdown` (the default).
* `B` interpreter binary to use, defaults to `auto` which guesses the best one.
* `FLOAT` should be formatted as `1` or `1.1` or `inf`. Note: command line
  argument also accepts a pair of timeouts.

#### Command-line arguments

<!--
``` python
!./python/bin/litrepl --help
```
-->

``` result
usage: litrepl [-h] [-v] [--filetype STR] [--python-interpreter EXE]
               [--ai-interpreter EXE] [--timeout F[,F]] [--propagate-sigint]
               [-d INT] [--verbose] [--auxdir DIR] [-C DIR]
               [--pending-exit INT] [--exception-exit INT] [--foreground]
               [--map-cursor LINE:COL:FILE] [--result-textwidth NUM]
               {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt}
               ...
positional arguments:
  {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt}
                              Commands to execute
    start                     Start the background interpreter.
    stop                      Stop the background interpreters.
    restart                   Restart the background interpreters.
    status                    Print background interpreter's status.
    parse                     Parse the input file (diagnostics).
    parse-print               Parse and print the input file back
                              (diagnostics, no changes are made).
    eval-sections             Parse stdin, evaluate the sepcified sections (by
                              default - all available sections), print the
                              resulting file to stdout.
    eval-code                 Evaluate the code snippet.
    repl                      Connect to the background terminal using GNU
                              socat.
    interrupt                 Send SIGINT to the background interpreter.
options:
  -h, --help                  show this help message and exit
  -v, --version               Print version.
  --filetype STR              Specify the type of input formatting
                              (markdown|[la]tex).
  --python-interpreter EXE    Python interpreter to use (python|ipython|auto)
  --ai-interpreter EXE        AI interpreter to use (aicli|auto).
  --timeout F[,F]             Timeouts for initial evaluation and for pending
                              checks, in seconds. If the latter is omitted, it
                              is considered to be equal to the former one.
  --propagate-sigint          If set, litrepl will relay SIGINT signals to the
                              running interpreter. Otherwise it just handles
                              them by itself.
  -d INT, --debug INT         Enable (a lot of) debug messages.
  --verbose                   Be more verbose (used in status).
  --auxdir DIR                Directory to store auxilary session files. By
                              default, the name of the aux. dir is derived
                              from the name of the current dir.
  -C DIR, --workdir DIR       Directory to run from, the current directory is
                              used by default.
  --pending-exit INT          Return this error code if whenever section hits
                              timeout.
  --exception-exit INT        Return this error code at exception, if any.
                              Note: it takes affect only for newly-started
                              interpreters.
  --foreground                Start a separate session and stop it when the
                              evaluation is done.
  --map-cursor LINE:COL:FILE  Calculate the new position of a cursor at
                              LINE:COL and write it to FILE.
  --result-textwidth NUM      Wrap result lines longer than NUM symbols.
```

### Applications

#### Command line, basic usage

To evaluate code section in a document:

```sh
$ cat doc/example.md | litrepl eval-sections >output.md
```

To evaluate a Python script:

```sh
$ cat script.py | litrepl eval-code
```

Note that both commands above share the same background interpreter session.


#### Command line, foreground evaluation

For batch processing of documents, it may be necessary to have an on-demand
interpreter session available, which would exist solely for the duration of the
evaluation process.

<!--lignore-->
~~~~ sh
$ cat document.md.in
``` python
raise Exception("D'oh!")
```
$ cat document.md.in | litrepl --foreground --exception-exit=200 eval-sections >document.md
$ echo $?
200
~~~~
<!--lnoignore-->

Here, the `--foreground` argument tells Litrepl to run a new interpreter session
and then stop it before exiting, `--exception-exit=200` sets the exit code
returned in the case of unhandled exceptions.

#### GNU Make, updating documentation

A typical Makefile recipe updating README.md might look as follows:

``` Makefile
.stamp_readme: $(SRC) Makefile
	cp README.md _README.md.in
	cat _README.md.in | \
		litrepl --foreground --exception-exit=100 --result-textwidth=100 \
		eval-sections >README.md
	touch $@

.PHONY: readme
readme: .stamp_readme
```

Where `$(SRC)` is supposed to contain valuable source filenames.

#### Vim, adding keybindings

The plugin does not define any keybindings, but users could do it by themselves,
for example:

``` vim
nnoremap <F5> :LEval<CR>
nnoremap <F6> :LEvalAsync<CR>
```

#### Vim, inserting new sections

Below we define `:C` command inserting new sections.

<!--lignore-->
``` vim
command! -buffer -nargs=0 C normal 0i``` python<CR>```<CR><CR>``` result<CR>```<Esc>4k
```
<!--lnoignore-->

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

#### Vim, executing text selection

Litrepl vim plugin defines `LitReplEvalSelection` function which runs the
selection as a virtual code section. The section type is passed as the function
argument.  For example, calling `LitReplEvalSelection('ai')` will execute the
selection as if it is an `ai` code section. The execution result is pasted right
after the selection as a plain text. `LitReplEvalSelection('python')` would pipe
the selection through the current Python interpreter.

To use the feature, define a suitable key binding (`Ctrl+K` in this example),

<!--lignore-->
``` vim
vnoremap <C-k> :call LitReplEvalSelection('ai')<CR>
```
<!--lnoignore-->

Now write a question to the AI in any document, select it and hit Ctrl+K.

~~~~
Hi model. What is the capital of New Zealand?
~~~~

Upon the keypress, Litrepl pipes the selection through the AI interpreter - the
`aicli` at the time of this writing - and paste the response right after the
last line of the original selection.

~~~~
Hi model. What is the capital of New Zealand?
The capital of New Zealand is Wellington.
~~~~

Internally, the plugin just uses `eval-code` Litrepl command.

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

``` shell
$ nix develop
```

will ask Nix to install the development dependencies and open the shell.

### Other Nix targets

Another shell which might be useful is `shell-screencast`. This would build the
full set of Litrepl tools and makes sure that the screencasting software is
available. To enter it, specify its Nix-flake path as follows:

``` shell
$ nix develop '.#shell-screencast'
```

To build individual Nix expressions, run `nix build '.#NAME'` passing the
name of Nix-expression to build. If succeeded, Nix publishes the last build'
results under the `./result` symlink.

``` shell
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

``` shell
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

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)

*Note: the below screencasts are outdated.*

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
* ~~Formatting: Special symbols in the Python output could invalidate the
  document~~.
* Interpreter: Extra newline is required after Python function definitions.
* Interpreter: Stdout and stderr are joined together.
* ~~Interpreter: Evaluation of a code section locks the editor~~.
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
* [Bad PDF fonts in Firefox](https://github.com/mozilla/pdf.js/issues/17401)


