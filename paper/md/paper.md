---
title: 'Litrepl: Literate Paper Processor Promoting Transparency More Than Reproducibility'
tags:
  - python
  - literate programming
  - human computer interaction
  - reproducible research
authors:
  - name: Sergei Mironov
    orcid: 0009-0005-1604-722X
    affiliation: 1
affiliations:
  - name: Independent Researcher, Armenia
    index: 1
date: 05 January 2025
bibliography: paper.bib
---

# Summary

Litrepl is a lightweight text processing tool designed to recognize and evaluate
code sections within Markdown or Latex documents. This functionality is useful
for both batch document section evaluation and interactive coding within a text
editor, provided a straightforward integration is established. Inspired by
Project Jupyter, Litrepl aims to facilitate the creation of research documents.
In the light of recent developments in software deployment, however, we have
shifted our focus from informal reproducibility to enhancing transparency in
communication with programming language interpreters, by either eliminating or
clearly exposing mutable states within the communication process.

# Statement of need

![Litrepl resource allocation diagram. Hash **A** is computed based on the Litrepl working directory and the interpreter class. Hash **B** is computed based on the contents of the code section.](./pic.png)


Literate Programming, formulated by Donald Knuth, shifts the focus from merely
coding to explaining computational tasks to humans. This approach is seen in the
WEB system [@Knuth1984lp] and its successor tools, which use a document format
that interleaves code sections with explanatory text. These systems can produce
both readable documentation and executable code, and over time, this concept has
evolved towards simplification [@Ramsey1994lps].

The Read-Evaluate-Print Loop (REPL), a key concept in human-computer
interaction, gained importance in the LISP and APL communities [@Spence1975apl],
[@McCarthy1959recfun], [@Iverson1962apl]. By combining a command-line interface
with a language interpreter, REPL enables incremental and interactive
programming, allowing users to modify the interpreter state directly. This
approach is believed to enhance human thought processes by keeping users
actively involved [@Granger2021litcomp].

A significant milestone in this field was the IPython interpreter
[@Perez2007IPython], which later evolved into the Jupyter Project. Its creators
introduced a new document format called the Jupyter Notebook [@Kluyver2016jupnb],
characterized by a series of logical sections of various types, including text
and code, which could directly interact with programming language interpreters.
This interactive communication, akin to REPL style programming, allows the
creation of well-structured documents suitable for presentations and sharing.
The concept underpinning these developments is termed *Literate Computing*
[@Perez2015blog], which includes goals of spanning a wide audience range,
boosting reproducibility, and fostering collaboration. To achieve these
objectives, several technical decisions were made, notably the introduction of
bidirectional communication between the computational core, known as the Jupyter
Kernel, and the Notebook web-based renderer, along with another layer of
client-server communication between the web-server and the user’s web browser.

While we recognize the importance of all goals within the Literate Computing
framework, we think that the goal of reproducibility is more important than
others. Addressing it alone would suffice to enhance communication among
time-separated and space-separated researchers and significantly expand the
audience. However, as it became clear [@Dolstra2010], this challenge extends
beyond the scope of a single human-computer interaction system, and even beyond
the typical boundaries of software distribution management for a particular
programming language. A comprehensive solution to the software deployment
problem operates at the entire operating system level.

Following [@Vallet2022], we propose shifting human-computer interaction towards
simplicity and transparency by introducing *Litrepl*. This tool offers
REPL-style editing, integrates with existing editors and text formats, and
minimizes hidden state variables, all while maintaining a compact codebase.
Litrepl uses bidirectional text streams for inter-process communication with
language interpreters and supports existing text formats like Markdown and LaTeX
through simplified parsers. It currently supports Python, Shell, and a custom
large language model interpreter, aiming to utilize POSIX [@POSIX2024] system
features extensively.

# How it works

Litrepl is implemented as a command-line text utility. Its primary function is
to take a text document as input, process it according to specified command-line
arguments and environment settings, and then output the resulting document
through its standard output.

The operation of Litrepl is best illustrated through the example below. Consider
the document named `input.tex`:

<!--
``` sh
echo '~~~ sh'
echo '$ cat input.tex'
cat input.tex
echo '~~~'
```
-->
<!--result-->
~~~ sh
$ cat input.tex
\begin{python}
import sys
print(f"I use {sys.platform} btw!")
\end{python}
\begin{result}
\end{result}
~~~
<!--noresult-->

This document contains a Python code section and an empty result section marked
with the corresponding Latex environment tags. To "execute" the document we
pipe it though the Litrepl processor as follows:

<!--
``` sh
echo '~~~ sh'
echo '$ cat input.tex | litrepl'
echo "sys.platform='linux'" | litrepl repl python >/dev/null
cat input.tex | litrepl
echo '~~~'
```
-->
<!--result-->
~~~ sh
$ cat input.tex | litrepl
\begin{python}
import sys
print(f"I use {sys.platform} btw!")
\end{python}
\begin{result}
I use linux btw!
\end{result}
~~~
<!--noresult-->

Now we can see the bold statement about the author's operating system. The
side-effect of this execution is the started session of the python interpreter
which is now running in the background. We can modify its state by adding more
section to the document and executing them selectively or e.g. by accessing
`litrepl repl python` terminal. So for example, setting `sys.platform` to
another value and re-evaluating the document would yield a different statement.


## Interfacing Interpreters

Litrepl communicates with interpreters using two uni-directional text streams:
one for writing input and another for reading outputs. To establish effective
communication, the interpreter should conform to the following general
assumptions:

* Synchronous single-user mode, which is implemented in most interpreters.
* A capability to disable command line prompts. Litrepl relies on the echo
  response, as described below, rather than on prompt detection.
* The presence of an echo command or equivalent. The interpreter must be able to
  echo an argument string provided by the user in response to the echo command.

## Session Management

Litrepl's ability to maintain interpreter sessions in the background is crucial
for enabling a Read-Eval-Print Loop (REPL) environment. The associated
resources, shown in Figure 1, are stored as files within an auxiliary directory.

If not specified by command-line arguments or environment variables, the
directory path is automatically derived from the interpreter class name, the
current working directory, and the OS's temporary file location.

The auxiliary directory includes two POSIX pipes for interpreter I/O and a file
recording the running interpreter's process ID, aiding session management.

When a code section is evaluated, Litrepl assigns a response file name derived
from hashing the code. This response file stores the output from the
interpreter.

During evaluation, Litrepl spawns a response reader process with a soft lock,
active until the interpreter completes and responds to an echo probe. The state
machine that operates the probe is the only added hidden state in the entire
system.

Litrepl provides **start**, **stop**, **restart** and **status** commands to
control background sessions, so, for example

``` sh
$ litrepl restart python
```

stops the Python interpreter if it was running and starts a new instance of it.
The **interrupt** command sends an interruption signal to the interpreter.
Finally, the **repl** command establishes direct communication with the
interpreter, allowing manual inspection of its state.


## Parsing and Evaluation

Litrepl abstracts documents as a straightforward sequence comprising code,
result, and text sections. Additionally, Litrepl identifies ignore blocks, which
act as comments that prevent enclosed sections from being evaluated.

Template grammars similar to the illustrative example below are encoded
for Markdown and Latex formats. Before each run, Litrepl calls Lark [@Lark] to
compile a customized parser and uses it to access the sections.

``` txt
document       ::= (code | result | ignore | text)*
code           ::= (code-normal | code-comment)
result         ::= (result-normal | result-comment)
code-normal    ::= "\begin{MARKER}" text "\end{MARKER}"
code-comment   ::= "% MARKER" text "% noMARKER"
result-normal  ::= "\begin{result}" text "\end{result}"
result-comment ::= "% result" text "% noresult"
ignore         ::= "% ignore" text "% noignore"
text           ::= ...
```

Evaluation results are written back into the result sections, and the entire
document is printed. At this stage, certain conditions can be optionally
checked. First, setting `--pending-exitcode` to a non-zero value instructs
Litrepl to report an error if a section takes longer than the timeout to
evaluate. Second, setting `--exception-exitcode` directs Litrepl to detect
Python exceptions. Lastly, `--irreproducible-exitcode` triggers an error if the
evaluation result doesn't match the text initially present in the result
section.

The last option implements the only formal check for aiding reproducibility that
Litrepl provides.


# Discussion


The technical decision to abstract interpreters using text streams comes with
both advantages and disadvantages. A key advantage is simplicity. However, there
are notable negative aspects. First, there is no parallel evaluation at the
communication level, meaning the interpreter is locked until it completes the
evaluation of one snippet before proceeding to the next. Second, the
transferable data type is restricted to text-only streams.

We argue that the lack of parallel execution at the communication level can be
mitigated using interpreter-specific parallelism, where supported. For instance,
Python programs can utilize various subprocess utilities, while shell programs
have full access to shell job control.

The restriction to text-only data types presents a more fundamental limitation.
Litrepl lifts this restriction by supporting text-only document formats. Both
Latex and Markdown incorporate non-text data without encoding it directly,
instead relying on references and side channels, such as the file system or
network resource identifiers. Consequently, Litrepl shares both the
benefits of human-readable representation in version control systems and the
penalties, such as the need to explicitly organize side-channel data transfer.

Another controversial technical decision is transferring the entire document as
input and output, which can negatively impact performance. Our experience shows
that the system performs adequately for documents of a few thousand lines.
However, larger documents may experience uncomfortable delays, even on modern
computers. Despite this, we choose to maintain this interface because it
simplifies editor integration. A typical plugin can pipe the whole document
through the tool using just a few lines of code.

A more performance-oriented integrations can make pre-parsing and pipe only
relevant document parts. For these approaches, Litrepl offers the `print-regexp`
command, which outputs the anchor regexp in several common formats.

# Conclusion

The tool is implemented in Python in under 2K lines of code according to the LOC
metric, and has only two Python dependencies so far, at the cost of the
dependency on the POSIX operating system interfaces. Needless to say, we used
Litrepl to evaluate and verify the examples presented in this document.

# References

