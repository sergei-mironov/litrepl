<div align="center">
<h1>
⌨️ LitRepl ⌨️
</h1>

[Changelog](./CHANGELOG.md) | [Installation](#-installation) | [Usage](#basic-execution) | [Gallery](#-gallery)

[![](./img/coverage.svg)](#-coverage-report)
</div>

<!--
``` python
!cat doc/description.md
```
-->
<!--result-->
**Litrepl** is a command-line processor for *Markdown* or *LaTeX* documents with
**literate programming** code sections. Instructed by its arguments, it
evaluates and updates sections via background interpreters. Interpreters can
stay active for a **read-eval-paste-loop** style. The repository includes a Vim
plugin to demonstrate editor integration.
<!--noresult-->

<div align="center">

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)

</div>


_Notes:_
* _[literate programming](https://en.wikipedia.org/wiki/Literate_programming)_
* _[read-eval-print-loop coding](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)_


<table border="0">
  <tr>
    <td>
      <a href="https://arxiv.org/abs/2501.10738">
        <img src="img/adobe_pdf.png" alt="PDF Icon">
      </a>
    </td>
    <td>
      Preprint: <i>(2025, Sergei Mironov)</i>
      <ins>Litrepl: Literate Paper Processor Promoting Transparency More Than Reproducibility</ins>
      <a href="https://arxiv.org/abs/2501.10738">arXiv:2501.10738</a>
    </td>
  </tr>
</table>

🔥 Features
-----------

* **Document formats** <br/>
  Markdown _(Example [[MD]](./doc/example.md))_ **|**
  [LaTeX](https://www.latex-project.org/)
  _(Examples [[TEX]](./doc/example.tex)[[PDF]](./doc/example.pdf))_
* **Interpreters** <br/>
  [Sh](https://en.wikipedia.org/wiki/Bourne_shell) **|**
  [Bash](https://www.gnu.org/software/bash/) **|**
  [Python](https://www.python.org/) **|**
  [IPython](https://ipython.org/) **|**
  [Aicli](https://github.com/sergei-mironov/aicli)
* **Editor integration** <br/>
  [Vim](https://www.vim.org/scripts/script.php?script_id=6117) _(plugin source included)_

✅ Requirements
---------------

* **POSIX-compatible OS**, typically a Linux. The tool relies on POSIX
  operations, notably pipes, and depends on certain Shell commands.
* **lark-parser** and **psutil** Python packages.
* **[Socat](http://www.dest-unreach.org/socat/)** (Optional) Needed for
  `litrepl repl` and Vim's `LTerm` commands to work.

📚 Contents
-----------

<!-- vim-markdown-toc GFM -->

* [🚀 Documentation](#-documentation)
* [🎥 Gallery](#-gallery)
* [📊 Coverage report](#-coverage-report)
* [💡 Technical Insights](#-technical-insights)
* [🚫 Known Limitations](#-known-limitations)
* [Related Tools and Projects](#related-tools-and-projects)
* [Considerations for Third-Party Tools](#considerations-for-third-party-tools)

<!-- vim-markdown-toc -->

🚀 Documentation
----------------

For documentation, visit the
[Github pages site](https://sergei-mironov.github.io/litrepl/).

* [Installation](https://sergei-mironov.github.io/litrepl/installation/)
* [Basic usage](https://sergei-mironov.github.io/litrepl/usage/general-concepts/)
* [Formatting documents](https://sergei-mironov.github.io/litrepl/usage/formatting/)

🎥 Gallery
----------

<details open>
<summary>Basic usage (Show GIF)</summary>

![Peek 2024-07-18 20-50-2](https://github.com/user-attachments/assets/8e2b2c8c-3412-4bf6-b75d-d5bd1adaf7ea)

</details>

<details>
<summary>AI capabilities (Show GIF)</summary>

![Peek 2024-11-28 20-48](https://github.com/user-attachments/assets/c91e6ac5-4230-47ad-b1bd-12b3d4d5f7f6)

</details>


<details>
<summary>Vimtex integration (Show Video)</summary>

We utilize LitRepl alongside the [Vimtex](https://github.com/lervag/vimtex) plugin to edit and
preview LaTeX documents instantly.

<video controls src="https://user-images.githubusercontent.com/4477729/187065835-3302e93e-6fec-48a0-841d-97986636a347.mp4" muted="true"></video>

</details>

📊 Coverage report
------------------

``` sh
coverage report --format=markdown -m
```

<!--result-->
| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| python/litrepl/\_\_init\_\_.py              |       34 |       12 |     65% |24-29, 35-40 |
| python/litrepl/base.py                      |      558 |       46 |     92% |48, 60, 78, 88, 137, 167, 207-213, 223, 229, 401, 412-413, 437-442, 450, 473, 499-500, 558, 615-616, 681-683, 727-736, 754-759 |
| python/litrepl/eval.py                      |      336 |      100 |     70% |36, 39-40, 49, 63, 67, 73, 77-78, 90-91, 93, 96-97, 101, 116, 118, 121-123, 126, 148-149, 151-152, 154, 156-159, 173-176, 179-183, 199, 205, 207, 212-223, 236, 249, 265-266, 277-280, 299-301, 317-319, 321, 326, 330, 335-339, 352, 364-370, 374-375, 381-382, 414, 420-423, 438, 442, 450, 454, 458, 465-471, 490-505 |
| python/litrepl/interpreters/\_\_init\_\_.py |        0 |        0 |    100% |           |
| python/litrepl/interpreters/aicli.py        |       50 |       19 |     62% |15-17, 37, 41-51, 60-66 |
| python/litrepl/interpreters/ipython.py      |       32 |        1 |     97% |        70 |
| python/litrepl/interpreters/python.py       |       22 |        1 |     95% |        38 |
| python/litrepl/interpreters/shell.py        |       22 |        1 |     95% |        26 |
| python/litrepl/main.py                      |      206 |       47 |     77% |22-24, 194, 197-200, 243, 252, 269-274, 276-278, 289-298, 311, 321-325, 334-342, 344-345, 351-352 |
| python/litrepl/revision.py                  |        1 |        1 |      0% |         2 |
| python/litrepl/semver.py                    |        1 |        1 |      0% |         2 |
| python/litrepl/types.py                     |       94 |        6 |     94% |137, 142, 148, 152, 156, 159 |
| python/litrepl/utils.py                     |       97 |        6 |     94% |37, 55, 129-132 |
|                                   **TOTAL** | **1453** |  **241** | **83%** |           |
<!--noresult-->

💡 Technical Insights
---------------------

The following events should normally happen after users type the `:LitEval1`
command:

1. On the first run, LitREPL starts the Python interpreter in the background.
   Its standard input and output are redirected into UNIX pipes in the current
   directory.
2. LitREPL runs the whole document through the express Markdown/Latex parser
   determining the start/stop positions of code and result sections. The cursor
   position is also available and the code from the right code section can
   reach the interpreter.
3. The process which reads the interpreter's response is forked out of the main
   LitREPL process. The output goes to the temporary file.
4. If the interpreter reports the completion quickly, the output is pasted to
   the resulting document immediately. Otherwise, the temporary results are
   pasted.
5. Re-evaluating sections with temporary results causes LitREPL to update
   these results.

🚫 Known Limitations
--------------------

* Formatting: Nested code sections are not supported.
* ~~Formatting: Special symbols in the Python output could invalidate the
  document~~.
* Interpreter: Extra newline is required after Python function definitions.
* Interpreter: Stdout and stderr are joined together.
* ~~Interpreter: Evaluation of a code section locks the editor~~.
* Interpreter: Tweaking `os.ps1`/`os.ps2` prompts of the Python interpreter
  could break the session.
* ~~Interpreter: No asynchronous code execution.~~
* ~~Interpreter: Background Python interpreter couldn't be interrupted~~

Related Tools and Projects
--------------------------

Edititng:

* https://github.com/lervag/vimtex (LaTeX editing, LaTeX preview)
* https://github.com/shime/vim-livedown (Markdown preview)
* https://github.com/preservim/vim-markdown (Markdown editing)

Code execution:

* Vim-medieval https://github.com/gpanders/vim-medieval
  - Evaluates Markdown code sections
* Pyluatex https://www.ctan.org/pkg/pyluatex
* Magma-nvim https://github.com/dccsillag/magma-nvim
* Codi https://github.com/metakirby5/codi.vim
* Pythontex https://github.com/gpoore/pythontex
  - Evaluates Latex code sections
* Codebraid https://github.com/gpoore/codebraid
* Vim-ipython-cell https://github.com/hanschen/vim-ipython-cell
* Vim-ipython https://github.com/ivanov/vim-ipython
* Jupytext https://github.com/goerz/jupytext.vim
  - Alternative? https://github.com/mwouts/jupytext
* Ipython-vimception https://github.com/ivanov/ipython-vimception

Useful Vim plugins:

* https://github.com/sergei-grechanik/vim-terminal-images (Graphics in vim terminals)

Useful tools:

* https://pandoc.org/

Considerations for Third-Party Tools
------------------------------------

* Vim-plug https://github.com/junegunn/vim-plug/issues/1010#issuecomment-1221614232
* Pandoc https://github.com/jgm/pandoc/issues/8598
* Jupytext https://github.com/mwouts/jupytext/issues/220#issuecomment-1418209581
* Vim-LSC https://github.com/natebosch/vim-lsc/issues/469
* [Bad PDF fonts in Firefox](https://github.com/mozilla/pdf.js/issues/17401)

