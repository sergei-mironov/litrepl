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


#### Vim, Calling for AI on a visual selection

The repository includes `litrepl_extras.vim`, which defines extra tools for
interacting with AI. These tools are based on the single low-level
`LitReplAIQuery()` function.

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
| `LAICont`  | Passes the prompt as-is        | Input, Selection       | Last               |
| `LAIStyle` | Asks to improve language style | Input, Selection       | Selection          |
| `LAICode`  | Asks to modify a code snippet  | Input, Selection       | Cursor, Selection  |
| `LAITell`  | Asks to describe a code snippet| Input, Selection       | Terminal*          |
| `LAIFile`  | Asks to change a whole file    | Input, Selection, File | File               |

* `LAITell` shows the response in the AI terminal instead of inserting it into
  the document.

As with the selection evaluation mode, the `aicli` interpreter stays
active in the background, maintaining the log of the conversation.

Direct interaction with the interpreter functions as expected. The `LTerm ai`
command opens the Vim terminal as usual, enabling communication with a model
through `aicli` text commands.


