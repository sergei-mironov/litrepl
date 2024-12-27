---
<!-- title: Litrepl: read-eval-print your literate papers -->
<!-- title: Litrepl: a minimalistic literate paper evaluation interface. -->
title: Litrepl: literate paper processor valuing transparency over reproducibility
tags:
  - python
  - literate programming
  - repl
  - reproducible research
authors:
  - name: Sergei Mironov
    orcid: TODO
    affiliation: "0"
date: 20 December 2024
bibliography: paper.bib
---

# Summary

Litrepl is a Python-based text processor designed to identify and evaluate code sections within
Markdown or LaTeX documents. Serving as middleware, Litrepl separates the logic of text editors from
programming language interpreter management. This separation encourages diversity in both text
editing environments and programming languages. As a result, Litrepl can become an integral
component of modular, "UNIX Way" inspired interactive development or typesetting systems.

# Statement of need

TODO: The plan:

1. The concept of Literate Programming was originally suggested by Donald Knuth
   - Main idea: explaining to human beings what we want a computer to do
   - Mention WEB, CWEB, NOWEB
   - Mention the focus on non-interactive ahead-of-time compilation
   - Mention two main modes of operation: weave and tangle
   - Mention the trend towards the simplification(?)

2. By that time, another human-computer interaction concept, read-evaluate-print-loop or REPL,
   already gained some popularity via the LISP developer community as well as via then-designed APL
   language for mathematical calculations. The command line interface combined with the language
   interpreter allowed incremental and, most importantly, interactive programming by directly
   changing the interpreter state. Keep human in the loop, thus, helps human to think.

3. The major milestone was the IPython project evolved later as the Jupyter Project. The creators
   suggested the new document format called Notebook represented by a series of logical sections of
   various types not limited to text, some of which contained code and some the computation results.
   The pairs of code and result sections of Notebooks are to communicate the programming language
   interpreter interactively, thus allowing REPL style programming. The resulting well-formed
   document allows readers to follow the narrative and is suitable for presentations and sharing.

   The authors formulated these ideas under the umbrella concept of Literate Computing, or building
   a computational narrative which is (1) spanning wide range of audience (2) bosting
   reproducibility and (3) collaboraiton.

   To fulfill these goals a number of technical decisions were made, the most important of these,
   along with the introduction of a new document format, are: the inter-module communication between
   the computational core, known as Jupyter Kernel, and the Notebook plaing the role of a client,
   another client-server communication between Notebook web-server and the user web-browser.

5. While we agree on the importance of concept of Literate Computing, but we argue that the goal of
   reproducibility overshadows other mentioned goals. Being solved, it would both allow
   time-separated communication between parties of a research project and widen its audience. Yet,
   we believe that this problem, as shown by [Doostra et al] exceeds not only the scope of
   human-computer interaction system but also the scope of a typical software distribution manager.
   for a particular programming language. An adequate solution to the softare deployment problem as
   Doostra called it, should span over a whole operating system scale.

6. For this reason, we suggest focusing human-computer interaction at transparency rahter than
   reproducibility. Below we describe ''Litrepl'' tool which is simple yet powerful to bring the
   REPL interactive programming style into the existing editors.

8. First, we suggest re-using the existing text document formats. In each of the two formats we
   implemented, Markdown and LaTeX, we use a simplified parsers to destinguish code and result
   sections from everything else. Second, we rely on the simple bi-directional text streams to
   communicate language interpreters via inter-process communication to evaluate code. At the time
   of this writing, we support families of Python and Shell interpreters and a custom AI
   communication interpreter. Finally, we leave as much as possible to the operating system
   facilities.

# How it works

7. Litrepl is designed as a command-line text processor in a way, making the integration into text
   editors as simple as passing the contents of the currently opened file through the utility. The
   repository provides an illustrative Vim plugin.

![](./pic.svg)

## Parsing

When the file appears on the Litrepl's stdin stream, it uses Earley parser to reliably recognize
   code and result sections.

## Evaluation

TODO

## Session management

TODO

## Session management

10. The tool is implemented in Python in about 2K lines of code according to the LOC metric, and has
    only two Python dependencies so far, at the cost of the dependency on the operating system
    intefaces for which we choose POSIX as a wide-spread openly available standard.

# References

