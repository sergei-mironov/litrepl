### Application Scenarios

#### Command Line, Foreground Evaluation

When performing batch processing of documents, it might be necessary to initiate
a new interpreter session solely for the evaluation's duration rather than
re-using the currently running session. The `--foreground` option can be used to
activate this mode.

<!--lignore-->
~~~~ shell
$ cat document.md.in | litrepl --foreground eval-sections > document.md
~~~~
<!--lnoignore-->

#### Command Line, Detecting Python Exceptions

Another frequently requested feature is the ability to report unhandled
exceptions. Litrepl can be configured to return a non-zero exit code in such
scenarios.

<!--lignore-->
~~~~ shell
$ cat document.md
``` python
raise Exception("D'oh!")
```
$ cat document.md | litrepl --foreground --exception-exit=200 eval-sections
$ echo $?
200
~~~~
<!--lnoignore-->

In this example, the `--foreground` option instructs Litrepl to start a new
interpreter session, stopping it upon completion. The `--exception-exit=200`
option specifies the exit code to be returned in the event of unhandled
exceptions.


#### Command Line, Running Remote Interpreters Over SSH

Litrepl supports running interpreters over SSH on a remote machine. In order to
do so, one needs to create a shell script establishing the communication and
name it in a recognizable way.

For example, consider the case where we edit a local document but all sections
that we want to execute should be run on a remote machine named `testbed`.

We prepare an executable script named `ipython-testbed.sh` and put it into a
directory listed in the PATH environment variable. The contents of the script is
the following:

```sh
#!/bin/sh
exec ssh testbed -p 22 -- bash --login -c ipython "$@"
```

Now, we can process our document as usual, but add `ipython-testbed.sh` as a new
IPython interpreter:

```sh
# Executes code sections on a remote machine.
cat README.md | litrepl --python-interpreter=ipython-testbed.sh
```

Note that the string `ipython` must appear in the interpreter name, to let
Litrepl exercise IPyhton-specific communication settings.

#### Command Line, Converting formatted Markdown to Jupyter Notebook

[Pandoc](https://pandoc.org) could be used to conver LitREPL-formatted markdown
documents to the Jupyter Notebook format. In order to make it recognize the code
and result fields, addtional formatting is required. Currently we aware of two
options:

##### Using fenced Markdown syntax extension

Mark Jupyter sections with fenced-div markup as described in the [Pandoc
manual](https://pandoc.org/MANUAL.html#jupyter-notebooks). Consider the
following `file.md`:

```` {.markdown}
:::::: {.cell .code execution_count=1}
```python
print("Hello Jupyter!")
```
::: {.output .stream .stdout}
``` result
Hello Jupyter!
```
:::
::::::
````

The above format is recognized by both `Litrepl` and `Pandoc`, so to
convert it to the Jupyter Notebook format one may run:

```sh
$ pandoc file.md -o file.ipynb
```

Unfortunately, other renderers may interpret fenced divs incorrectly.

##### Using Native divs syntax extension

Alternatively, native divs syntax extension could be used. Consider the
following `file.md` file:

````
<div class="cell code">
```python
print("Hello Jupyter!")
```

<div class="output stream stdout">
```result
Hello Jupyter!
```
</div>
</div>
````

Both `Litrepl` and `Pandoc` will recognize this format, plus most third-party
renderers will ignore `div` tags. The downside of this approach is the fact that
pandoc now needs [native divs
extension](https://pandoc.org/MANUAL.html#extension-native_divs) to convert the
document:

```sh
$ pandoc -f markdown+native_divs file.md -o test.ipynb
```

#### Command Line, Latex In-PDF code highliting with Minted

The following Latex instructions can be used to properly highlight the code and
result sections. Note, that `pygmentize` system tool needs to be installed in
the system.

``` tex
\usepackage{minted}
\renewcommand{\MintedPygmentize}{pygmentize}

% LitREPL-compatible environment for Python code snippets
\newenvironment{python}
  {\VerbatimEnvironment
   \begin{minted}[autogobble,breaklines,fontsize=\footnotesize]{python}}
  {\end{minted}}
\BeforeBeginEnvironment{python}{\begin{mdframed}[nobreak=false,everyline=true]}
\AfterEndEnvironment{python}{\end{mdframed}}

% LitREPL-compatible ai secitons
\newenvironment{ai}
  {\vsp\textbf{User:}\vsp}
  {}
\newenvironment{airesult}
  {\vsp\textbf{AI:}\vsp}
  {}

% LitREPL-compatible environment for code results
\newenvironment{result}
  {\VerbatimEnvironment
   \begin{minted}[autogobble,breaklines,fontsize=\footnotesize]{text}}
  {\end{minted}}
\BeforeBeginEnvironment{result}{\begin{mdframed}[nobreak=true,frametitle=\tiny{Result}]}
\AfterEndEnvironment{result}{\end{mdframed}}

% LitREPL-compatible command for inline code results
\newcommand{\linline}[2]{#2}
\newcommand{\st}[1]{\sout{#1}}
\renewcommand{\t}[1]{\texttt{#1}}
```

Hint: Use `\usepackage[outputdir=_build]{minted}` if you specify a separate
build directory (here - `_build`). This workarounds a well-known Minted problem.


#### GNU Make, Evaluating Code Sections in Project Documentation

A typical Makefile recipe for updating documentation is structured as follows:

``` Makefile
SRC = $(shell find -name '*\.py')

.stamp_readme: $(SRC) Makefile
	cp README.md _README.md.in
	cat _README.md.in | \
		litrepl --foreground --exception-exit=100 \
                --python-interpreter=ipython \
                --sh-interpreter=- \
		eval-sections >README.md
	touch $@

.PHONY: readme
readme: .stamp_readme
```

Here, `$(SRC)` is expected to include the filenames of dependencies. With this
recipe, we can run `make readme` to evaluate the python sections. By passing `-`
wealso tell Litrepl to ignore shell sections.


#### Vim, Setting Up Keybindings

The `litrepl.vim` plugin does not define any keybindings, but users could do it
by themselves, for example:

``` vim
nnoremap <F5> :LEval<CR>
nnoremap <F6> :LEvalAsync<CR>
```

#### Vim, Inserting New Sections

The `litrepl.vim` plugin doesn't include tools for creating section formatting,
however they can be added easily if required. Below, we demonstrate how to
define the `:C` command inserting new `python` sections.

<!--lignore-->
```` vim
command! -buffer -nargs=0 C normal 0i``` python<CR>```<CR><CR>``` result<CR>```<Esc>4k
````
<!--lnoignore-->
<!---``` <- to make TokOpen() happy -->

#### Vim, Running the Initial Section After Interpreter Restart

Below we demonstrate how to define the `:LR` command for running first section
after the restart.

``` vim
command! -nargs=0 LR LRestart | LEval 0
```

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


#### Vim, In-Editor Latex code highlighting with Vimtex

The following `.vimrc` Vimtex configuration enables highlighting of Python
code sections in LaTeX documents. We typically need to call these functions from
the `BufEnter` event handler.

``` vim
" .localvimrc
call vimtex#syntax#nested#include('python')
call vimtex#syntax#core#new_region_env('texLitreplZone', 'l[a-zA-Z0-9]*code',
  \ {'contains': '@vimtex_nested_python'})
```


#### Vim, Calling for AI on a visual selection

_Note: `litrepl_extras.vim` has been reworked since 3.14.0._

_Note: this is not stable and a subject to change._

The repository includes `litrepl_extras.vim`, which defines a generic
interface for external text‑rewriting tools. While it can work with a variety
of backends, it is primarily designed to integrate smoothly with
[Aicli](https://github.com/sergei-mironov/aicli) sessions powered by Litrepl.

The `litrepl_extras.vim` defines the following Vim commands:

- `:LPush[!] <script> <prompt>` Calls the `litrepl-<script>` executable and
  echoes its output.
- `:LPipe[!] <script> <prompt>` pipes the selection through the
  `litrepl-<script>` executable (if there is a selection) or inserts the
  executable's output at the cursor position.
- `:LPipeFile[!] <script> <prompt>` pipes the current file through the
  `litrepl-<script>` executable (if there is a selection) or inserts the
  executable's output at the cursor position.


All the above commands get translated into a command line matching
the following convension (subject to change):

~~~ sh
usage: litrepl-<script> [-h] [-P PROMPT_LIST] [-s SELECTION_PASTE]
                        [-S SELECTION_RAW] [-f OUTPUT_FORMAT] [-w TEXTWIDTH]
                        [-v] [--location NAME LOC]
                        [--location-raw NAME LOC] [--command COMMAND]
                        ...

positional arguments:
  files

options:
  -h, --help            show this help message and exit
  -P PROMPT_LIST, --prompt PROMPT_LIST
  -s SELECTION_PASTE, --selection-paste SELECTION_PASTE
  -S SELECTION_RAW, --selection-raw SELECTION_RAW
  -f OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
  -w TEXTWIDTH, --textwidth TEXTWIDTH
  -v, -d, --debug, --verbose
  --dry-run
  --location NAME LOC
  --location-raw NAME LOC
  --command COMMAND
~~~

The `command` is currently set to the fixed `eval-code` string literal.

The bang versions of the Vim commands cause `-S` (disable escaping commands
within the selection) to be used instead of `-s` (escape the selection). For
Aicli this means that the /commands would be executed rather than passed to an
LLM model.

Users are free to write their own scripts. The completion will try to match
the `litrepl-*` pattern to a unique match. For example, below is the example
of the `litrepl-grammar.sh` script, which asks AI to correct the grammar of
the selected text:

~~~ sh
#!/bin/sh

exec litrepl-aicli.py -P "Please correct English grammar within the 'selection'. Keep the choice of words, minimize the changes you make." "$@"
~~~
