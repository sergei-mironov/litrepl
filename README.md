LitREPL.vim
------------

**LitREPL** is a VIM plugin and a Python library for Litrate programming and
code evaluation right inside the editor.

<img src="./demo.gif" width="400"/>

Requirements:

* Unix-compatible OS. The plugin depends on unix pipes and certain shell commands.
* More or less recent Vim
* Python3 with the following libraries:
  - lark-parser
  - ~~pylightnix~~

Known limitations:

* Synchronous Python execution only
* The plugin tweaks prompts of the Python interpreter
* Read buffer is set to a constant `1024`

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
3. Open a Markdown file, put the cursor on the Python code section (see the
   *Formatting* section below). Execute the `:LitEval1` command. The following
   events should happen:
   1. On the first run, the Python interpreter will be started in the
      background. Its standard input and output will be redirected into UNIX
      pipes in the current directory. Its PID will be saved into the
      `./_pid.txt` file.
   2. The code from the Markdown code section under the cursor will be piped
      through the interpreter.
   3. The result will be pasted into the Markdown section next after the current
      one.

   The state of the Python interpreter is persistent. To restart the session,
   use `:LitStop`/`:LitStart` commands

Formatting
----------

### Markdown

Verbatim markdown sections with the `python` annotation are considered as
executable sections. If the executable section is followed by a verbatim section
without tags, this section is used for pasting the execution results. Examples
are:

```python
W='Hello, world!'
print(W)
```

Put the cursor on the above section and run the `:LitEval1` command. The result
should appear in the section below.

```
Hello, world!
```

Now run the `:LitEval1` command again on the next section to re-use the
interpreter state. The result section next to the executable one will be
updated.

```python
print(W[:7]+"LitREPL.vim!")
```

```
Hello, LitREPL.vim!
```

### Latex

TODO

