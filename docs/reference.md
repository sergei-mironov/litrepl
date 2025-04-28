### Command Reference

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

* `T` Type of the interpreter: `python`, `ai` or `sh` (some commands also accept `all`)
* `F` Path to a Markdown or LaTeX file
* `P` Path to a Python script
* `N` Number of code section to evaluate, starting from 0.
* `L:C` denotes line:column of the cursor.

#### Command Line Arguments and Vim Variables

| Vim setting  <img width=200/>   | CLI argument  <img width=200/> | Description                       |
|---------------------------------|--------------------------------|-----------------------------------|
| `set filetype`                  | `--filetype=T`                 | Input file type: `latex`\|`markdown` |
| `let g:litrepl_python_interpreter=B` | `--python-interpreter=B`  | The Python interpreter to use |
| `let g:litrepl_ai_interpreter=B`     | `--ai-interpreter=B`      | The AI interpreter to use |
| `let g:litrepl_sh_interpreter=B`     | `--sh-interpreter=B`      | The shell interpreter to use |
| `let g:litrepl_python_auxdir=D` | `--python-auxdir=D`            | The auxiliary files directory used by Python interpreter |
| `let g:litrepl_ai_auxdir=D`     | `--ai-auxdir=D`                | The auxiliary files directory used by AI interpreter |
| `let g:litrepl_sh_auxdir=D`     | `--sh-auxdir=D`                | The auxiliary files directory used by a shell interpreter |
| `let g:litrepl_workdir=D`       | `--workdir=D`                  | The auxiliary files directory used by AI interpreter |
| `let g:litrepl_debug=0/1`       | `--debug=0/1`                  | Print debug messages to the stderr |
| `let g:litrepl_timeout=FLOAT`   | `--timeout=FLOAT`              | Timeout to wait for the new executions, in seconds, defaults to inf |

* `T` Type of the document: `tex` or `markdown` (the default).
* `B` Interpreter command to use, `-` or `auto` (the default). `-` value
  disabled this type of interpreters; `auto` asks litrep to guess the best
  available interpreter.
* `D` Filesystem directory
* `FLOAT` Should be formatted as `1` or `1.1` or `inf`. Note: command line
  argument also accepts a pair of timeouts.

#### Command Line Arguments Summary

<!--
``` python
!./python/bin/litrepl --help
```
-->

``` result
usage: litrepl [-h] [-v] [--filetype STR] [--python-markers STR[,STR]]
               [--ai-markers STR[,STR]] [--sh-markers STR[,STR]]
               [--python-interpreter EXE] [--ai-interpreter EXE]
               [--sh-interpreter EXE] [--python-auxdir DIR] [--ai-auxdir DIR]
               [--sh-auxdir DIR] [--timeout F[,F]] [--propagate-sigint]
               [-d INT] [--verbose] [-C DIR] [--pending-exitcode INT]
               [--irreproducible-exitcode INT] [--exception-exitcode INT]
               [--foreground] [--map-cursor LINE:COL:FILE]
               [--result-textwidth NUM]
               {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt,print-regexp,print-grammar,print-auxdir}
               ...

positional arguments:
  {start,stop,restart,status,parse,parse-print,eval-sections,eval-code,repl,interrupt,print-regexp,print-grammar,print-auxdir}
                              Commands to execute
    start                     Start a background interpreter. The CLASS of an
                              interpreter should be specified.
                              --<CLASS>-interpreter, --<CLASS>-auxdir etc. are
                              applied.
    stop                      Stop the background interpreters.
    restart                   Restart the background interpreters.
    status                    Print background interpreter's status.
    parse                     Parse the input file without futher processing
                              (diagnostics).
    parse-print               Parse and print the input file back
                              (diagnostics).
    eval-sections             Parse stdin, evaluate the specified sections (by
                              default - all available sections), print the
                              resulting file to stdout.
    eval-code                 Evaluate the code snippet.
    repl                      Connect to the background terminal using GNU
                              socat.
    interrupt                 Send SIGINT to the background interpreter.
    print-regexp              Print regexp matching start of code sections for
                              the given file type.
    print-grammar             Print the resulting grammar for the given
                              filetype.
    print-auxdir              Print the auxdir for the given interpreter type.

options:
  -h, --help                  show this help message and exit
  -v, --version               Print version.
  --filetype STR              Specify the type of input formatting
                              (markdown|[la]tex|auto).
  --python-markers STR[,STR]  Specify section markers recognized as `python`
                              sections. Defaults to the value of
                              LITREPL_PYTHON_MARERS if set, otherwize
                              "python".
  --ai-markers STR[,STR]      Specify section markers recognized as `ai`
                              sections. Defaults to the value of
                              LITREPL_AI_MARERS if set, otherwize "codeai,ai".
  --sh-markers STR[,STR]      Specify section markers recognized as `shell`
                              sections. Defaults to the value of
                              LITREPL_SH_MARERS if set, otherwize "shell".
  --python-interpreter EXE    Python interpreter command line, or `auto`.
                              Defaults to the LITREPL_PYTHON_INTERPRETER
                              environment variable if set, otherwise "auto".
                              Litrepl determines "python" or "ipython" type
                              according to the value.
  --ai-interpreter EXE        `aicli` interpreter command line or `auto`.
                              Defaults to the LITREPL_AI_INTERPRETER
                              environment variable if set, otherwise "auto".
  --sh-interpreter EXE        Shell interpreter command line or `auto`.
                              Defaults to the LITREPL_SH_INTERPRETER
                              environment variable if set, otherwise "auto".
  --python-auxdir DIR         This directory stores Python interpreter pipes.
                              It defaults to LITREPL_PYTHON_AUXDIR if set;
                              otherwise, it's created in the system's
                              temporary directory, named after the current
                              working directory.
  --ai-auxdir DIR             This directory stores AI interpreter pipes. It
                              defaults to LITREPL_AI_AUXDIR if set; otherwise,
                              it's created in the system's temporary
                              directory, named after the current working
                              directory.
  --sh-auxdir DIR             This directory stores AI interpreter pipes. It
                              defaults to LITREPL_SH_AUXDIR if set; otherwise,
                              it's created in the system's temporary
                              directory, named after the current working
                              directory.
  --timeout F[,F]             Timeouts for initial evaluation and for pending
                              checks, in seconds. If the latter is omitted, it
                              is considered to be equal to the former one.
  --propagate-sigint          If set, litrepl will catch and resend SIGINT
                              signals to the running interpreter. Otherwise it
                              will just terminate itself leaving the
                              interpreter as-is.
  -d INT, --debug INT         Enable (a lot of) debug messages.
  --verbose                   Be more verbose (used in status).
  -C DIR, --workdir DIR       Set the working directory before execution. By
                              default, it uses LITREPL_WORKDIR if set,
                              otherwise remains the current directory. This
                              affects the directory of a new interpreter and
                              the --<interpreter>-auxdir option.
  --pending-exitcode INT      Return this error code if whenever a section
                              hits timeout.
  --irreproducible-exitcode INT
                              Return this error code if a section outputs a
                              different result than the one that is already
                              present in the document.
  --exception-exitcode INT    Return this error code at exception, if any.
                              Note: this option might not be defined for some
                              interpreters. It takes affect only for newly-
                              started interpreters.
  --foreground                Start a separate session and stop it when the
                              evaluation is done. All --*-auxdir settings are
                              ignored in this mode.
  --map-cursor LINE:COL:FILE  Calculate the new position of a cursor at
                              LINE:COL and write it to FILE.
  --result-textwidth NUM      Wrap result lines longer than NUM symbols.
```

