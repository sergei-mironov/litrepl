Changelog
=========

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

