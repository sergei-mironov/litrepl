<!--
vim: tw=80
--!>
Changelog
=========

Version 3.13.0
--------------

1. **Python**
   - Improved backward compatibility by fixing issues related to spurious
     newlines on empty inputs.
   - Accept `codeai` code section for AI interpreters, in addition to `ai`.
   - Introduced a new command `print-auxdir`.

2. **Environment**
   - Added support for generating coverage reports with updates to the Makefile.
   - Added dependency on coverage-badge, enhancing reporting capabilities.
   - Modified settings to ignore empty `LITREPL_` environment variables.

3. **Vim**
   - Enhanced the indentation feature in Litrepl to preserve empty lines.
   - Updated the status command to print the auxiliary directory and fixed an
     unwanted exception.

Version 3.12.0
--------------

1. **Python**
   - Fix the hashing algorithm to exclude the unstable `hash()` output from
     digests thus fixed an issue with handling a `None` suffix in digests,
     improving the stability and accuracy of digest computations.
   - Section addressing has been adjusted to start from 1 instead of 0 for
     readability.
   - Made `eval-sections` the default command, reflecting a focus on ease of use
     and user interaction.

2. **Environment**
   - Underscores have been removed from auxiliary directory file names.
   - Add a link to the arXiv [paper](https://arxiv.org/abs/2501.10738).

3. **Vim**
   - Added new options for ignoring specific LaTeX sections with the `lignore`
     feature, enhancing customization for LaTeX users.
   - Updated the Vim async tag pattern `BG` -> `LR`.


Version 3.11.0
--------------

1. **Python**
   - The interpreters have been refactored into their own submodule, improving
     code organization.
   - Added preliminary support for
     [shell](./python/litrepl/interpreters/shell.py) interpreters, allowing the
     system to handle shell commands.
   - Introduced new commands: `print-grammar` to output the grammar and
     `print-regexp` for regular expression management.
   - Introduced adjustable code section labels, removing the default `lcode`
     sections support.
   - Improved debugging and configuration support in IPython by ensuring
     expanded paths and correct handling of the DEBUG setting.
   - Support for automatic file type detection with `--filetype=auto` has been
     implemented.
   - The support for `--irreproducible-exitcode` argument was added

2. **Vim**
   - Fixed cursor handling issues in `LEvalMon`, improving text navigation and
     evaluation feedback within Vim.
   - Improve error reporting performed by the `LOpenErr` command.

Version 3.10.1
--------------

Minor environment changes

Version 3.10.0
--------------

1. **Python**
   - Code refactoring for better code management and efficiency: moved main
     logic in `litrepl` from `python/bin/litrepl` to a new file
     [python/litrepl/main.py](./python/litrepl/main.py).
   - Improved handling of subprocess management for the Python and AI
     interpreters, ensuring proper cleanup and output management. Additionally,
     calls to `os.system` were mostly replaced with native Python calls.
   - Added robust error handling and message retrieval for the interpreter
     interface, providing clearer errors when the interpreter fails.

2. **Vim**
   - Introduced the default environment variable check for `LITREPL_WORKDIR`,
     `LITREPL_PYTHON_AUXDIR`, `LITREPL_AI_AUXDIR` etc. environment variables.
   - Updated Vim functions to consider both buffer and global settings,
     improving flexibility in command generation (`LitReplGet` helper function).
   - Updated commands related to AI tasks like `:LAIStyle`, `:LAIFile`, and
     `:LAICode` to handle rephrasing and AI interaction more efficiently.
   - Adjusted internal Vim functions to handle text width settings and cursor
     positionings.

3. **Environment**
   - Replaced `test.sh` with [runtests.sh](./sh/runtests.sh) in the build and test
     process for enhanced test execution flow.
   - Allowed more environment configuration by introducing more settings that
     default from environment variables, streamlining setup customization.
   - Updated Nix build script ([default.nix](./default.nix)) to reflect changes
     in the test script location and hash updates for source verification.
   - Added this changelog and the AI-powered changelog helper script
     [diffchanges.sh](./sh/diffchanges.sh).

Version 3.9.0
-------------

1. **Python**
   - Added assertions to ensure a successful attachment to the interpreter,
     enhancing error handling robustness.

2. **Vim**
   - Enhanced [vim/plugin/litrepl.vim](./vim/plugin/litrepl.vim) by preserving
     caret positions and restructuring comments for function alignment.
   - Significant expansions in
     [vim/plugin/litrepl_extras.vim](./vim/plugin/litrepl_extras.vim) with
     multiple new functions for region handling, AI task management, and
     interaction across different scopes, substantially improving user
     experience with AI functionalities in Vim. Several new commands such as
     `LAITell`, `LAICont`, `LAIStyle`, `LAIFile`, and `LAICode` are introduced
     to support a wide range of code and AI-related tasks.

3. **Environment**
   - Added a new markdown file `./doc/screencast.md` with examples for
     evaluating Python code in Vim, offering insights into the screencast
     documentation process.
   - Adjusted `screencast.sh` to be executable and made improvements to
     accommodate a target file parameter.
   - Introduced a new test function `test_vim_ai_query` in `test.sh`,
     facilitating new test coverage for AI query functionality.

