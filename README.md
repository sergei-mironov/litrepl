LitRepl
=======

**LitRepl** is a command-line tool that brings together the benefits of
[literate programming](https://en.wikipedia.org/wiki/Literate_programming) and
[read-eval-print-loop coding](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop).
LitREPL comes bundled with an interface Vim plugin, integrating it into the editor.

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)


🔥 Features
-----------

* **Document formats** <br/>
  Markdown _(Example [[MD]](./doc/example.md))_ **|**
  [LaTeX](https://www.latex-project.org/)
  _(Examples [[TEX]](./doc/example.tex)[[PDF]](./doc/example.pdf))_
* **Interpreters** <br/>
  [Python](https://www.python.org/) **|**
  [IPython](https://ipython.org/) **|**
  [Aicli](https://github.com/sergei-mironov/aicli)
* **Editor integration** <br/>
  Vim _(plugin included)_

<details><summary><h2>✅ Requirements</h2></summary><p>

* POSIX-compatible OS, typically a Linux. The tool relies on POSIX operations, notably pipes, and
  depends on certain Shell commands.
* Python packages: `lark-parser`, `psutil` (Required).
* [socat](https://linux.die.net/man/1/socat) (Optional, only required for
  `litrepl repl` and Vim's LRepl commands). The tool is widely accessible on
  Unix systems.

</p></details>

📚 Contents
-----------

<!-- vim-markdown-toc GFM -->

* [⚙️ Installation](#-installation)
* [🚀 Usage](#-usage)
    * [General Concepts](#general-concepts)
        * [Basic Execution](#basic-execution)
        * [Selecting Sections for Execution](#selecting-sections-for-execution)
        * [Managing Interpreter Sessions](#managing-interpreter-sessions)
        * [Asynchronous Processing](#asynchronous-processing)
        * [Direct Interaction with Interpreters](#direct-interaction-with-interpreters)
        * [Experimental AI Features](#experimental-ai-features)
        * [Calling for AI on a Vim visual selection](#calling-for-ai-on-a-vim-visual-selection)
    * [Application Scenarios](#application-scenarios)
        * [Command Line, Foreground Evaluation](#command-line-foreground-evaluation)
        * [GNU Make, Automating Code Section Processing](#gnu-make-automating-code-section-processing)
        * [Vim, Setting Up Keybindings](#vim-setting-up-keybindings)
        * [Vim, Inserting New Sections](#vim-inserting-new-sections)
        * [Vim, Running the Initial Section After Interpreter Restart](#vim-running-the-initial-section-after-interpreter-restart)
        * [Vim, Executing Shell Commands](#vim-executing-shell-commands)
        * [Vim, Evaluating Selected Text](#vim-evaluating-selected-text)
    * [In-Depth Reference](#in-depth-reference)
        * [Vim Commands and Command-Line Attributes](#vim-commands-and-command-line-attributes)
        * [Command Line Arguments and Vim Variables](#command-line-arguments-and-vim-variables)
        * [Command Line Arguments Summary](#command-line-arguments-summary)
* [🏗️ Development Guidelines](#-development-guidelines)
    * [Building Targets](#building-targets)
    * [Development Environments and Setup](#development-environments-and-setup)
    * [Tools for Screencast Recording](#tools-for-screencast-recording)
    * [Common Development Techniques](#common-development-techniques)
* [🎪 Visual Showcases](#-visual-showcases)
* [💡 Technical Insights](#-technical-insights)
* [🚫 Known Limitations](#-known-limitations)
* [Related Tools and Projects](#related-tools-and-projects)
* [Considerations for Third-Party Tools](#considerations-for-third-party-tools)

<!-- vim-markdown-toc -->

⚙️ Installation
--------------

This repository contains the Litrepl tool, packaged as both a standalone Python
application and a Vim plugin interface. The author's preferred method is using
Nix, but if you choose not to use it, you'll need to install both components
separately. Below, we outline several common installation methods.

<details><summary><b>Release versions, from Pypi and Vim.org</b></summary><p>

1. `pip install litrepl`
2. Download the `litrepl.vim` from the vim.org
   [script page](https://www.vim.org/scripts/script.php?script_id=6117) and put it into
   your `~/.vim/plugin` folder.

</p></details>

<details><summary><b>Latest versions, from Git, using Pip and Vim-Plug</b></summary><p>

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

<details><summary><b>Latest versions, from source, using Nix</b></summary><p>

The repository offers a suite of Nix expressions designed to optimize
installation and development processes on systems that support Nix. Consistent
with standard practices in Nix projects, the [flake.nix](./flake.nix) file
defines the source dependencies, while the [default.nix](./default.nix) file
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

Nix are used to open the development shell, see the [Development](#development)
section.

</p></details>

<details><summary><b>Latest versions, from source, using Pip</b></summary><p>

The Litrepl application might be installed with `pip install .` run from the
project root folder. The Vim plugin part requires hand-copying
`./vim/plugin/litrepl.vim` and `./vim/plugin/litrepl_extras.vim` to the `~/.vim`
config folder.

</p></details>

The Nix-powered installation methods install the Socat tool automatically. For
other installation methods, use your system pacakge manager to install it. For
example, Ubuntu users might run `sudo apt-get install socat`.

🚀 Usage
--------

### General Concepts

The Litrepl tool identifies code and result sections within a text document. It
processes the code by sending it to the appropriate interpreters and populates
the result sections with their responses. The interpreters remain active in the
background, ready to handle new inputs.

Litrepl supports Markdown and LaTeX formatting and also can treat plain code
as a single code section.

At present, Litrepl includes support for two Python interpreter variants and a
custom Aicli interpreter by the same author.

#### Basic Execution

Litrepl recognises and executes verbatim code sections followed by zero or more
result sections. In Markdown documents, the Python code is any triple-quoted
section labeled as `python`. The result is any triple-quoted `result` section.
In LaTeX documents, sections are marked with `\begin{python}\end{python}` and
`\begin{result}\end{result}` environments correspondingly.

The primary command for evaluating formatted documents is `litrepl
eval-sections`. To execute the evaluation, redirect the file into the shell
command's input.

Consider a document named `source.md`:

<!--lignore-->
~~~~ markdown
``` python
print('Hello Markdown!')
```
``` result
```
~~~~

You pass it to Litrepl using:

~~~~ shell
$ cat source.md | litrepl eval-sections > result.md
~~~~

The resulting `result.md` will have the result section filled in correctly.

~~~~ markdown
``` python
print('Hello Markdown!')
```
``` result
Hello Markdown!
```
~~~~
<!--lnoignore-->

By default, `litrepl eval-sections` evaluates all sections. The Vim equivalent
command is `:LEval`, which by default evaluates the section at the cursor.

* For additional details on Markdown formatting, refer to [Formatting Markdown
  documents](./doc/formatting.md#markdown)

By default, Litrepl assumes Markdown formatting. Use the `--filetype=tex` option
to change the format to LaTeX. The Vim plugin automatically handles this based
on the `filetype` variable. Here is how the earlier example would appear in
LaTeX:

~~~~ tex
\begin{python}
print('Hello LaTeX!')
\end{python}

\begin{result}
Hello LaTeX!
\end{result}
~~~~

- LaTeX documents usually require a preamble to introduce python/result tags to
  the TeX processor. For more information, see [Formatting LaTeX
  documents](./doc/formatting.md#latex).


#### Selecting Sections for Execution

Both `eval-sections` command-line command and `:LEval` vim command takes
an optional argument that specifies which sections to evaluate. The overall
command-line syntax is `litrepl eval-sections WHICH`, where `WHICH` can be:

* `N`: Represents a specific code section to evaluate, with the following
  possible formats:
  - A number starting from 0.
  - `$`, indicating the last section.
  - `L:C`, referring to the line and column position. Litrepl calculates the
    section number based on this position.
* `N..N`: Represents a range of sections, determined using the rules mentioned
  above.

In addition to the above generic format, the `:LEval` of Vim accepts the
following strings: `all`, `above` (the cursor) and `below` (the cursor).

#### Managing Interpreter Sessions

Each interpreter session uses an auxiliary directory where Litrepl stores
filesystem pipes and other runtime data.

By default, the directory name is derived from the current directory name (for
Vim, this is based on the directory of the current file).

This behavior can be configured by:
* Explicitly setting the working directory with `--workdir=DIR` (this may also
  affect the current directory of the interpreters), or
* Defining the auxiliary directory with `--<interpreter-type>-auxdir=DIR`


The commands `litrepl start`, `litrepl stop`, and `litrepl restart` are used to
manage interpreter sessions. They accept the interpreter type to operate on or
the keyword `all` to apply the command to all interpreters. Add the
`--<interpreter-type>-interpteter=CMDLINE` to set the exact command line for
Litrepl to execute.

``` shell
$ litrepl start python
$ litrepl restart ai
$ litrepl stop all
```

The equivalent Vim commands are `:LStart`, `:LStop`, and `:LRestart`. For the
corresponding Vim configuration variables, see the reference section below.


The `litrepl status` command queries the information about the currently running
interpreters running. The command reveals the process PID and the command-line
arguments. For stopped interpreters, the last exit codes are also listed.


``` shell
$ litrepl status
# Format:
# TYP  PID      EXITCODE  CMD
python 3900919  -         python3 -m IPython --config=/tmp/litrepl_1000_a2732d/python/litrepl_ipython_config.py --colors=NoColor -i
ai     3904696  -         aicli --readline-prompt=
```

The corresponding Vim command is `:LStatus`.

#### Asynchronous Processing

Litrepl can generate an output document before the interpreter has finished
processing. If the evaluation takes longer than a timeout, Litrepl leaves a
marker, enabling it to continue from where it was stopped during future runs.
The `--timeout=SEC[,SEC]` option allows you to set timeouts. The first number
specifies the initial execution timeout in seconds, while the optional second
number sets the timeout for subsequent attempts. By default, both timeouts are
set to infinity.

For instance, executing `litrepl --timeout=3.5 eval-sections` on the
corresponding program yields:

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

Upon re-executing the document, Litrepl resumes processing from the marker. Once
evaluation concludes, it removes the marker from the output section.

The command `litrepl interrupt` sends an interrupt signal to the interpreter,
prompting it to return control sooner (with an exception).

- The equivalent Vim commands are `:LEvalAsync` (defaulting to a 0.5-second
  timeout) and `:LInterrupt`.
- The Vim plugin also provides the `:LEvalMon` command, which facilitates
  continuous code evaluation with no delay. Interrupting this with Ctrl+C will
  make Litrepl return control to the editor, leaving the evaluation ongoing in
  the background.


#### Direct Interaction with Interpreters

The command `litrepl repl [TYPE]` where `TYPE` stands for `python` (the default)
or `ai`, connects to interpreter sessions, enabling users to interact with them
directly.  For this command to work, [socat](https://linux.die.net/man/1/socat)
tool needs to be installed on your system. Litrepl blocks the pipes for the time
of interaction so no evaluation is possible while the repl session is active.
For Python interpreter, the command prompt is disabled which is a current technical
limitation. All other interpreter functionality is kept unchanged. Use `Ctrl+D`
to safely detach the session. For example:

``` shell
$ litrepl repl python
Opening the interpreter terminal (NO PROMPTS, USE `Ctrl+D` TO DETACH)
W = 'Hello from repl'
^D
```

- The equivalent Vim commands are `:LRepl [TYPE]` or `:LTerm [TYPE]`. Both
  commands open Vim terminal window.
- Python prompts are internally disabled, so no `>>>` symbols will appear.

Use `litrepl eval-code [TYPE]` to direct code straight to the interpreter,
bypassing any section formatting steps. In contrast to the `repl` command,
`eval-code` mode features prompt detection, allowing the tool to display the
interpreter's response and detach while keeping the session open.

For example, after manually defining the `W` variable in the example above, it
can be queried as in a typical IPython session.

``` shell
$ echo 'W' | litrepl eval-code
'Hello from repl'
```

The `eval-code` command can be utilized for batch processing and managing
sessions, in a manner similar to how the `expect` tool is used.

#### Experimental AI Features

Litrepl experimentally supports [Aicli](https://github.com/sergei-mironov/aicli)
terminal allowing users to query external language models. In order to try it,
install the interpreter and use `ai` as the name for code sections. For
low-speed models it might be convenient to use `:LEvalMon` command to monitor
the text generation in real time.

<!--lignore-->
~~~~ markdown
``` ai
/model gpt4all:"./_models/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
Hi chat! What is your name?
```

``` result
I'm LLaMA, a large language model trained by Meta AI. I'm here to help answer
any questions you might have and provide information on a wide range of topics.
How can I assist you today?
```
~~~~
<!--lnoignore-->

All Aicli `/`-commands like the `/model` command above are passed as-is to the
interpreter. The `/ask` command is added automatically at the of each section,
so make sure that `ai` secions have self-contained questions.

As a pre-processing step, Litrepl can paste text from other sections of the
document in place of special reference markers. The markers have the following
format:

* `>>RX<<`, where `X` is a number - references a section number `X` (starting
  from zero).
* `^^RX^^`, where `X` is a number - references the section `X` times above the
  current one.
* `vvRXvv`, where `X` is a number - references the section `X` times below the
  current one.

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


#### Calling for AI on a Vim visual selection

The repository includes [litrepl_extras.vim](./vim/plugin/litrepl_extras.vim), which
defines extra tools for interacting with AI. These tools are based on the single
low-level `LitReplAIQuery()` function.

The function enables the creation of an AI chat query possibly incorporating the
current file and any selected text. The AI model's response then returned
alongside with the Litrepl error code.


Based on this function, the following two middle-level functions are defined:
- `LitReplTaskNew(scope, prompt)`
- `LitReplTaskContinue(scope, prompt)`

Both functions take the prompt, produce the AI model response and decide where
to insert it. However, the key difference is that the first function determines
the target location based on user input (like cursor position or selection),
while the second function re-applies the previously used position, allowing
users to make changes easilly.

Finally, a number of high-level commands have been established. Each of these
commands receives an input string that directs the model on what action to take.
The user input can contain `/S` or `/F` tokens, which are replaced with the
values of the visual selection and the current file, respectively.


| Command    | Description                    | Incorporates           | Updates            |
|------------|--------------------------------|------------------------|--------------------|
| `LAI`      | Passes the prompt as-is        | Input, Selection       | Cursor, Selection  |
| `LAICont`  | Passes the prompt as-is        | Input, Selection       | Last |
| `LAIStyle` | Asks to improve language style | Input, Selection       | Selection          |
| `LAICode`  | Asks to modify a code snippet  | Input, Selection       | Cursor, Selection  |
| `LAITell`  | Asks to describe a code snippet| Input, Selection       | Terminal*          |
| `LAIFile`  | Asks to change a whole file    | Input, Selection, File | File               |

* `LAITell` displays the response in the AI terminal

As with the selection evaluation mode, the `aicli` interpreter stays
active in the background, maintaining the log of the conversation.

Direct interaction with the interpreter functions as expected. The `LTerm ai`
command opens the Vim terminal as usual, enabling communication with a model
through `aicli` text commands.

### Application Scenarios

#### Command Line, Foreground Evaluation

When performing batch processing of documents, it might be necessary to initiate
a new interpreter session solely for the evaluation's duration. The
`--foreground` option can be used to activate this mode.

Another frequently requested feature is the ability to report unhandled
exceptions. Litrepl can be configured to return a non-zero exit code in such
scenarios.

<!--lignore-->
~~~~ sh
$ cat document.md.in
``` python
raise Exception("D'oh!")
```
$ cat document.md.in | litrepl --foreground --exception-exit=200 eval-sections
>document.md
$ echo $?
200
~~~~
<!--lnoignore-->

In this example, the `--foreground` option instructs Litrepl to start a new
interpreter session, stopping it upon completion. The `--exception-exit=200`
option specifies the exit code to be returned in the event of unhandled
exceptions.


#### GNU Make, Automating Code Section Processing

A typical Makefile recipe for updating README.md is structured as follows:

``` Makefile
SRC = $(shell find -name '*\.py')

.stamp_readme: $(SRC) Makefile
	cp README.md _README.md.in
	cat _README.md.in | \
		litrepl --foreground --exception-exit=100 \
		eval-sections >README.md
	touch $@

.PHONY: readme
readme: .stamp_readme
```

Here, `$(SRC)` is expected to include the filenames of dependencies. By using
this recipe, you can execute `make readme` to start the processing.


#### Vim, Setting Up Keybindings

The plugin does not define any keybindings, but users could do it by themselves,
for example:

``` vim
nnoremap <F5> :LEval<CR>
nnoremap <F6> :LEvalAsync<CR>
```

#### Vim, Inserting New Sections

Below we define `:C` command inserting new sections.

<!--lignore-->
```` vim
command! -buffer -nargs=0 C normal 0i``` python<CR>```<CR><CR>``` result<CR>```<Esc>4k
````
<!--lnoignore-->
<!---``` <- to make TokOpen() happy -->

#### Vim, Running the Initial Section After Interpreter Restart

We define the `:LR` command running first section after the restart.

``` vim
command! -nargs=0 LR LRestart | LEval 0
```

#### Vim, Executing Shell Commands

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

#### Vim, Evaluating Selected Text

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

### In-Depth Reference

#### Vim Commands and Command-Line Attributes

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
| `:LTerm [T]`         | `lirtepl repl [T]`               | Connect to the interpreter using GNU socat |
| `:LOpenErr`          | `litrepl ...  2>F`               | View errors |
| `:LVersion`          | `litrepl --version`              | Show version |

Where

* `T` type of the interpreter: `python` or `ai` (some commands also accept `all`)
* `F` Path to a Markdown or LaTeX file
* `P` Path to a Python script
* `N` number of code section to evaluate, starting from 0.
* `L:C` denotes line:column of the cursor.

#### Command Line Arguments and Vim Variables

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

#### Command Line Arguments Summary

<!--
``` python
!./python/bin/litrepl --help
```
-->

``` result
usage: litrepl [-h] [-v] [--filetype STR] [--python-interpreter EXE]
               [--ai-interpreter EXE] [--timeout F[,F]] [--propagate-sigint]
               [-d INT] [--verbose] [--python-auxdir DIR] [--ai-auxdir DIR]
               [-C DIR] [--pending-exit INT] [--exception-exit INT]
               [--foreground] [--map-cursor LINE:COL:FILE]
               [--result-textwidth NUM]
               {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt}
               ...

positional arguments:
  {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt}
                              Commands to execute
    start                     Start the background interpreter.
    stop                      Stop the background interpreters.
    restart                   Restart the background interpreters.
    status                    Print background interpreter's status.
    parse                     Parse the input file without futher processing
                              (diagnostics).
    parse-print               Parse and print the input file back
                              (diagnostics).
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
  --propagate-sigint          If set, litrepl will catch and resend SIGINT
                              signals to the running interpreter. Otherwise it
                              will just terminate itself leaving the
                              interpreter as-is.
  -d INT, --debug INT         Enable (a lot of) debug messages.
  --verbose                   Be more verbose (used in status).
  --python-auxdir DIR         Directory to store Python interpreter pipes. By
                              default, it is created in the system temporary
                              directory with the name derived from current
                              working directory.
  --ai-auxdir DIR             Directory to store AI interpreter pipes. By
                              default, it is created in the system temporary
                              directory with the name derived from current
                              working directory.
  -C DIR, --workdir DIR       Set the new current working directory before
                              run. Note that changing directory has the
                              following effects: (1) changes directory of the
                              newly started interpreter (2) influence the
                              default --<interp>-auxdir.
  --pending-exit INT          Return this error code if whenever a section
                              hits timeout.
  --exception-exit INT        Return this error code at exception, if any.
                              Note: this option might not be defined for some
                              interpreters. It takes affect only for newly-
                              started interpreters.
  --foreground                Start a separate session and stop it when the
                              evaluation is done.
  --map-cursor LINE:COL:FILE  Calculate the new position of a cursor at
                              LINE:COL and write it to FILE.
  --result-textwidth NUM      Wrap result lines longer than NUM symbols.
```


🏗️ Development Guidelines
-------------------------

This project uses [Nix](https://nixos.org/nix) as its main development
framework. The file [flake.nix](./flake.nix) manages the source-level
dependencies required by Nix, whereas [default.nix](./default.nix) specifies
common build targets, including PyPI and Vim packages, demo Vim configurations,
development shells, and more.

### Building Targets

To build individual Nix expressions, execute the command `nix build '.#NAME'`,
replacing `NAME` with the actual name of the Nix expression you want to build.
If the build is successful, Nix places the results of the last build in a
symbolic link located at `./result`.

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

See `local.collection` attribute-set in the [default.nix](./default.nix) for the
full list of defined targetr.

For example, to build a version of Vim pre-configured for demo, run

``` shell
$ nix build '.#vim-demo'
$ ./result/bin/vim-demo  # Run the pre-configured demo instance of Vim
```

### Development Environments and Setup

The default development shell is defined in the `./default.nix` as a Nix
expression named `shell` which is the default name for development shells.
Running

``` shell
$ nix develop
```

will ask Nix to install the development dependencies and open shell.

### Tools for Screencast Recording

Another shell which might be useful is `shell-screencast`. This would build the
full set of Litrepl tools and makes sure that the screencasting software is
available. To enter it, specify its Nix-flake path as follows:

``` shell
$ nix develop '.#shell-screencast'
```

In the opened shell, run the `screencast.sh` and wait a second, until the script
arranges demo and recorder wondows.

``` shell
$ screencast.sh
```

`screencast.sh` accepts an optional parameter specifying the template file to
open for the recording session.

### Common Development Techniques

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

🎪 Visual Showcases
-------------------

Basic usage

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)

*Note: the below screencasts are outdated.*

Using LitREPL in combination with the [Vimtex](https://github.com/lervag/vimtex)
plugin to edit Latex documents on the fly.

<video controls src="https://user-images.githubusercontent.com/4477729/187065835-3302e93e-6fec-48a0-841d-97986636a347.mp4" muted="true"></video>

Asynchronous code execution

<img src="https://user-images.githubusercontent.com/4477729/190009000-7652d544-a668-4440-933d-799f3410736f.gif" width="510"/>


💡 Technical Insights
---------------------

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

🚫 Known Limitations
--------------------

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

Related Tools and Projects
--------------------------

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

Considerations for Third-Party Tools
------------------------------------

* Vim-plug https://github.com/junegunn/vim-plug/issues/1010#issuecomment-1221614232
* Pandoc https://github.com/jgm/pandoc/issues/8598
* Jupytext https://github.com/mwouts/jupytext/issues/220#issuecomment-1418209581
* Vim-LSC https://github.com/natebosch/vim-lsc/issues/469
* [Bad PDF fonts in Firefox](https://github.com/mozilla/pdf.js/issues/17401)


