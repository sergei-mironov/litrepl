LiteREPL.vim
------------

**LiteREPL** is a VIM plugin for literate programming and code evaluation right
inside the editor.

*The plugin is currently is at the proof-of-concept stage. No code is packaged,
use this repository to reproduce results*

Requirements:

* Vim
* Unix-comatible system. Unix pipes and shell commands are heavily used.
* Python3 with the following libraries:
  - lark
  - ~~pylightnix~~

Setup
-----

1. `git clone --recursive <https://this_repo>; cd literepl.vim`
2. Source the environment `. env.sh`. Read warnings and install python packages
   which could be missing. The file will add `./sh` and `./python` to the PATH,
   the former contains VIM wrapper adding the plugin, the latter contains Python
   script
3. Open a Markdown file, put the cursor on the Python code section (see
   *Formatting* section below), execute the `:LitEval1` command. The following
   events should happen:
   1. Python interpreter will be started in the background. Its standard input
      and output will be redirected into UNIX pipes in the current
      directory. Its PID will be saved into the `./_pid.txt` file.
   2. The code from the code section would be piped through the interpreter.
   3. The result of the execution will be pasted into the result Markdown
      section which should present in the current file.
   4. The state of the Python interpreter is persistent. To restart the session,
      use `:LitStop`/`:LitStart` commands

Formatting
----------

### Markdown

The verbatim sections with the `python` annotation are considered as executable
sections. If the executable section is followed by another verbatim section
without the tag, this section is used for pasting the execution results. Example
formatting:

```python
W='Hello, world'
print(W)
```

```
<Result>
```

```python
print(W[:6]+"LiteREPL.vim!")
```

```
<Result 2>
```

### Latex

TODO

