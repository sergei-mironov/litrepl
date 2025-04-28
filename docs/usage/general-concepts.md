## General concepts

The Litrepl tool identifies code and result sections within a text document. It
processes the code by sending it to the appropriate interpreters and populates
the result sections with their responses. The interpreters remain active in the
background, ready to handle new inputs.

Litrepl supports subsets of **Markdown** and **LaTeX** formatting in order to
recognize the sections. Some aspects of the recognized grammars, such as section
labels, could be configured.

#### Basic Execution

Litrepl searches for verbatim code sections followed by zero or more result
sections. In Markdown documents, the Python code is any triple-quoted section
with a pre-configured label such as `python`. The result is any triple-quoted
`result` section.  In LaTeX documents, sections are marked with
`\begin{...}\end{...}` environments correspondingly.

The primary command for evaluating formatted documents is `litrepl
eval-sections`. Consider a [hello.md](../static/hello.md) document:

<!--
``` python
print("~~~~ markdown")
!cat docs/static/hello.md
print("~~~~")
```
-->

<!-- result -->
~~~~ markdown
``` python
print('Hello Markdown!')
```
``` result
```
~~~~
<!-- noresult -->

You pass it to Litrepl using:

~~~~ shell
$ cat hello.md | litrepl eval-sections > result.md
~~~~

The `result.md` will have all sections filled in correctly.
<!--
``` python
print("~~~~ markdown")
!cat docs/static/hello.md | litrepl --foreground eval-sections
print("~~~~")
```
-->

<!-- result -->
~~~~ markdown
``` python
print('Hello Markdown!')
```
``` result
Hello Markdown!
```
~~~~
<!-- noresult -->

* For additional details on Markdown formatting, refer to [Formatting Markdown
  documents](./formatting.md#markdown)

Similarly, in a LaTeX document, we format code and result sections as follows:

~~~~ tex
\begin{python}
print('Hello LaTeX!')
\end{python}

\begin{result}
Hello LaTeX!
\end{result}
~~~~

- LaTeX documents require a preamble introducing python/result environments to
  the TeX processor. For more information, see [Formatting LaTeX
  documents](./formatting.md#latex).

By default, Litrepl tried to guess the format of the input document. Use the
`--filetype=(latex|markdown)` option to set the format explicitly:

``` sh
$ cat doc.md | litrepl --filetype=markdown eval-sections
$ cat doc.tex | litrepl --filetype=latex eval-sections
```

* The main Vim command for code section evaluation is `:LEval`. By default, it
  executes the section at the cursor. To execute all sections in a document, use
  `:LEval all`.

#### Selecting Sections for Execution

By default, `litrepl eval-sections` evaluates all sections in a document. To
evaluate only specific sections, the range argument should be specified. The
overall syntax is `litrepl eval-sections [RANGE]`, where `RANGE` can be:

* `N`: Represents a specific code section to evaluate, with the following
  possible formats:
  - A number starting from `0`.
  - `$` symbol, indicating the last section.
  - `L:C`, referring to the line and column position. Litrepl calculates the
    section number based on this position.
* `N..N`: Represents a range of sections, determined using the rules mentioned
  above.

Some examples:

``` sh
$ litrepl eval-sections '0'       # First section in a document
$ litrepl eval-sections '3..$'    # Sections from fourth section (zero based) to the last one
$ litrepl eval-sections '34:1..$' # Sections starting from line 34 column 1
```

* The Vim command `:LEval` accepts similar syntax and also recognizes specific
  keywords `all`, `above`, and `below`. These keywords allow you to evaluate all
  sections, only those above the cursor, or just the ones below the cursor,
  respectively.

#### Managing Interpreter Sessions

Each interpreter session uses an auxiliary directory where Litrepl stores
filesystem pipes and other runtime data.

By default, the auxiliary directory path is derived from the working directory
name (for Vim, this defaults to the directory of the current file).

This behavior can be configured by:
* Setting the working directory with `LITREPL_WORKDIR` environment
  variable or `--workdir=DIR` command-line argument (this may also affect the
  current directory of the interpreters), or
* Explicitly setting the auxiliary directory with `LITREPL_<CLASS>_AUXDIR`
  environment variable or `--<class>-auxdir=DIR` command-line argument, where
  `<class>` stands for either `python`, `ai` or `sh`.


The commands `litrepl start CLASS`, `litrepl stop [CLASS]`, and `litrepl restart
[CLASS]` are used to manage interpreter sessions. They accept the interpreter
type to operate on or (for some commands) the keyword `all` to apply the command
to all interpreters. Add the `--<class>-interpteter=CMDLINE` to adjust the
command line to run, but be careful - Litrepl adds more arguments to configure
prompts and verbosity to some interpreters, notably to the pythons.

``` sh
$ litrepl --python-interpreter=ipython start python
$ litrepl --sh-interpreter=/opt/bin/mybash start sh
$ litrepl restart all
$ litrepl stop
```

* The equivalent Vim commands are `:LStart CLASS`, `:LStop [CLASS]`, and
  `:LRestart [CLASS]`. For the corresponding Vim configuration variables, see
  the reference section below.


The `litrepl status [CLASS]` command queries the information about the currently
running interpreters. The command reveals the process PID and the command-line
arguments. For stopped interpreters, the last exit codes are also listed.
Specifying `CLASS` prints the status for this class of interpreters only.

``` sh
$ litrepl status
# Format:
# CLASS  PID      EXITCODE  CMD
python   3900919  -         python3 -m IPython --config=/tmp/litrepl_1000_a2732d/python/litrepl_ipython_config.py --colors=NoColor -i
ai       3904696  -         aicli --readline-prompt=
```

* The corresponding Vim command is `:LStatus`. No `CLASS` argument is currently
  supported.

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

* The equivalent Vim commands are `:LEvalAsync` (defaulting to a 0.5-second
  timeout) and `:LInterrupt`.
* The Vim plugin also provides the `:LEvalMon` command, which facilitates
  continuous code evaluation with no delay. Interrupting this with Ctrl+C will
  make Litrepl return control to the editor, leaving the evaluation ongoing in
  the background.


#### Attaching Interpreter Sessions

The command `litrepl repl [CLASS]` where `CLASS` specifies interpreter class:
`python` (the default) `ai` or `sh`, attaches to interpreter sessions.  For this
command to work, [socat](https://linux.die.net/man/1/socat) tool needs to be
installed on your system. Litrepl blocks the pipes for the time of interaction
so no evaluation is possible while the repl session is active.  For Python and
Shell interpreters, the command prompt is disabled which is a current technical
limitation. Use `Ctrl+D` to safely detach the session. For example:

``` sh
$ litrepl repl python
Opening the interpreter terminal (NO PROMPTS, USE `Ctrl+D` TO DETACH)
W = 'Hello from repl'
^D
$
```

Use `litrepl eval-code [CLASS]` to direct code straight to the interpreter,
bypassing any section formatting steps. In contrast to the `repl` command,
`eval-code` mode features prompt detection, allowing the tool to display the
interpreter's response and detach while keeping the session open.

For example, after manually defining the `W` variable in the example above, it
can be queried as in a typical IPython session.

``` sh
$ echo 'W' | litrepl eval-code
'Hello from repl'
```

The `eval-code` command can be utilized for batch processing and managing
sessions, in a manner similar to how the `expect` tool is used.

* The equivalent Vim commands are `:LRepl [CLASS]` or `:LTerm [CLASS]`. Both
  commands open Vim terminal window.

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


