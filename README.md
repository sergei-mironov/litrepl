LitREPL.vim
------------

**LitREPL** is a VIM plugin and a Python library for Litrate programming and
code evaluation right inside the editor.

<img src="./demo.gif" width="400"/>

Requirements:

* Linux-compatible OS. The plugin depends on UNIX pipes and certain shell
  commands.
* More or less recent `Vim`
* `Python3` with the following libraries:
  - lark-parser
  - ~~pylightnix~~
* `socat` application

Known limitations:

* Python code blocks are evaluated synchronously.
* No support for nested code sections.
* No escaping: unlucky Python output could result in the invalid Markdown
* Tweaking `os.ps1`/`os.ps2` prompts of the Python interpreter could break the
  session.
* ~~Background Python interpreter couldn't be interrupted~~

_Currently, the plugin is at the proof-of-concept stage. No code is packaged,
clone this repository to reproduce the results!_

Setup
-----

1. `git clone --recursive <https://this_repo>; cd litrepl.vim`
2. Enter the development environment
   * (For Nix/NixOS systems) `nix-shell`
   * (For other Linuxes) `. env.sh`
   Read the warnings and install the missing packages if required. The
   environment script will add `./sh` and `./python` folders to the current
   shell's PATH.  The former folder contains the back-end script, the latter one
   contains the back-end script.
3. Run the `vim_litrepl_dev` (a thin wrapper around Vim) to run the Vim with the
   LitREPL plugin from the `./vim` folder.

Vim Commands
------------

* `:LitStart`/`:LitStop`/`:LitRestart` - Starts, stops or restarts the
  background Python interpreter
* `:LitEval1` - Execute the executable section under the cursor, or the
  executable section of the result section under the cursor
* `:LitRepl` - Open the Vim terminal exclusively connected to the Python
  interpreter via `socat` tool. This way user could inspect it's state. Note,
  that standard Python prompts `>>>`/`...` are disabled.

Formatting
----------

### Markdown

````
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

TODO

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



