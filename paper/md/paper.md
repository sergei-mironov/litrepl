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
clearly exposing mutable states within the communication process. The tool is
designed to ensure easy code editor integration, and the project repository
offers a reference Vim plugin.

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

A pivotal development in this field was the IPython interpreter
[@Perez2007IPython], which led to the Jupyter Project and its Jupyter Notebook
format [@Kluyver2016jupnb]. This format consists of logical sections like text
and code that can interact with language interpreters, enabling REPL-like
programming for well-structured, shareable documents. This is part of *Literate
Computing* [@Perez2015blog], which aims to reach broad audiences, enhance
reproducibility, and promote collaboration. Key technical aspects include
bidirectional communication between the Jupyter Kernel and Notebook renderer,
alongside client-server interactions between the web server and user browser.

We believe that reproducibility is crucial in the Literate Computing framework,
enhancing communication among dispersed researchers. However, as illustrated by
[@Dolstra2010], we argue that this challenge exceeds the capacity of a single
system, needing operating system-level solutions. Following [@Vallet2022], we
introduce *Litrepl*, which enables REPL-style editing by integrating with existing
editors and formats, and reduces hidden state variables in a compact codebase.
Litrepl uses bidirectional text streams for inter-process communication and
supports Markdown and LaTeX formats with simplified parsers. It supports Python,
Shell, and a custom large language model communication interpreter while
leveraging POSIX [@POSIX2024] system features.

The difference between Litrepl and other solutions, including Jupyter, is
highlighted in the table below.

| Name        | Document formats   | Data formats | Interpreters | Backend                      | Frontend             |
|-------------|--------------------|--------------|--------------|------------------------------|----------------------|
| Jupyter     | Jupyter[j1]        | Rich         | Many[j2]     | Client-server via ZeroMQ[j3] | Web, Editor          |
| Quarto      | Markdown+[q1]      | Rich         | Few          | Modified Jupyter[q2]         | Web, Editor          |
| Codebraid   | Markdown+[c1]      | Rich         | Many[c2]     | Same as Jupyter[c3]          | Editor               |
| R markdown  | Markdown+[r1]      | Rich         | Few[r2]      | Linked libraries[r3]         | Editor               |
| Litrepl     | Markdown, LaTeX    | Text-only    | Few          | POSIX Pipes                  | Command line, Editor |


* [Jupyter](https://jupyter.org/)
  - [j1] [Jupyter Notebook Format](https://nbformat.readthedocs.io/en/latest/)
  - [j2] [Available kernels](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels)
  - [j3] Details on Jupyter backend communication [link](https://docs.jupyter.org/en/latest/projects/kernels.html)
* [Quarto](https://quarto.org/docs/tools/text-editors.html)
  - [q1] [Quarto Markdown extensions](https://quarto.org/docs/computations/execution-options.html)
  - [q2] Quarto uses the slightly modified Jupyter kernel protocol. See
    [Jupyter kernel support](https://quarto.org/docs/advanced/jupyter/kernel-execution.html)
    [Qurto echo kernel](https://github.com/quarto-dev/quarto_echo_kernel/blob/b77fde70c25a869175cc225a3676eee2df5a1733/README.rst)
* [Codebraid](https://codebraid.org/)
  - [c1] Codebraid Markdown extensions are described as
    [code chunks formatting](https://codebraid.org/code_chunks/)
  - [c2] Codebraid supports Jupyter kernels [link](https://github.com/gpoore/codebraid/blob/3f85800bd58c2a1587778a1fe0f24c46dc1c3a69/README.md?plain=1#L13-L16)
  - [c3] Codebraid supports interactive editing via Jupyter kernels.
* [R markdown](https://rmarkdown.rstudio.com/)
  - [r1] The [R Markdown language](https://bookdown.org/yihui/rmarkdown/)
  - [r2] In RMarkdown most languages do not share a session between code sections, the exceptions
    are R, Python and Julia
    [link](https://github.com/rstudio/rmarkdown-book/blob/521044173f39aee2c2f646f0712dfcdd6c22e214/02-basics.Rmd#L589)
  - [r3] For Python, RMarkdown relies on [Reticulate](https://github.com/rstudio/rmarkdown-book/blob/521044173f39aee2c2f646f0712dfcdd6c22e214/02-basics.Rmd#L603) to run 
    which uses low-level Python features to organize the communication [link](https://github.com/rstudio/reticulate/blob/9f50ca05d3f0d478241944d925f8f931c8661817/src/event_loop.cpp#L15).


# How it works

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
print(f"I use {sys.platform.upper()} btw!")
\end{python}
\begin{result}
\end{result}
~~~
<!--noresult-->

This document contains a Python code section and an empty result section marked
with the corresponding LaTeX environment tags. To "execute" the code sections of
the document, we pipe the whole document through the Litrepl processor as
follows (only the last three relevant lines of the result are shown).

<!--
``` sh
echo '~~~ sh'
echo '$ cat input.tex | litrepl eval-sections 1 | tail -n 3'
echo "sys.platform='linux'" | litrepl repl python >/dev/null
cat input.tex | litrepl | tail -n 3
echo '~~~'
```
-->
<!--result-->
~~~ sh
$ cat input.tex | litrepl eval-sections 1 | tail -n 3
\begin{result}
I use LINUX btw!
\end{result}
~~~
<!--noresult-->

The side effect of this execution is the starting of a session with the Python
interpreter, which now runs in the background. We communicate with it by editing
the document and re-running the above command.

Evaluation results are written back into the result sections, and the entire
document is printed. At this stage, certain conditions can be optionally
checked. First, adding `--pending-exitcode=INT` instructs Litrepl to report an
error if a section takes longer than the timeout to evaluate. Second, setting
`--exception-exitcode=INT` directs Litrepl to detect Python exceptions. Lastly,
`--irreproducible-exitcode=INT` triggers an error if the evaluation result
doesn't match the text initially present in the result section.


## Interfacing Interpreters

Litrepl communicates with interpreters using POSIX uni-directional streams, one
for writing input and another for reading outputs. During the communication,
Litrepl makes the following general assumptions:

* The streams implement synchronous single-user mode.
* Command line prompts are disabled. Litrepl relies on the echo response, as
  described below, rather than on prompt detection.
* The presence of an echo command or equivalent. The interpreter must be able to
  echo an argument string provided by the user in response to such command.

The simplicity of this approach is a key advantage, but it also has drawbacks.
There's no parallel evaluation at the communication level, locking the
interpreter until each snippet is evaluated. This can be addressed by using
interpreter-specific parallelism, such as Python's subprocess utilities or shell
job control. The text-only data type limitation is more fundamental; Litrepl
overcomes this by supporting text-only document formats. Formats like LaTeX and
Markdown handle non-text data via references or side channels (e.g., file
systems), balancing benefits in version control with the need for explicit data
transfer organization.

## Session Management

Litrepl maintains interpreter sessions in the background to support a REPL
environment. Resources are stored in an auxiliary directory specified by
command-line arguments, environment variables, or automatically derived paths.
This directory contains pipe files for I/O and a file with the interpreter's
process ID for session management. When evaluating code, Litrepl creates a
response file named by hashing the code to store interpreter output. A response
reader process with a soft lock runs until the interpreter finishes and responds
to a probe, introducing the system's only hidden state.

# Conclusion

The tool is implemented in Python in under 2K lines of code according to the LOC
metric, and has only two Python dependencies so far, at the cost of the
dependency on the POSIX operating system interfaces. Needless to say, we used
Litrepl to evaluate and verify the examples presented in this document.

# References

