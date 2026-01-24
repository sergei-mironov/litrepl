## Vim plugin

Litrepl comes with a reference Vim plugin, which interfaces Litrepl using its
command-line interface.

As specified in the [Reference](../reference.md) section, the plugin mirrows most modes of
operation by its commands, that typically starts from capital `L`. Many options
are also mirrored by the vim variables.

### Installation

#### Installing release versions from Vim.org

Download the latest `vim-litrepl-*.tar.gz` from the vim.org [script
page](https://www.vim.org/scripts/script.php?script_id=6117) and unpack it into
your `~/.vim` folder with  `tar -xf vim-litrepl-*.tar.gz  -C ~/.vim`

#### Installing latest versions from Git using Vim-Plug

Install the Vim plugin by adding the following line between the
`plug#begin` and `plug#end` lines of your `.vimrc` file:
```vim
Plug 'https://github.com/sergei-mironov/litrepl' , { 'rtp': 'vim' }
```
Note: `rtp` sets the custom vim-plugin source directory of the plugin.

#### Installing latest versions from source using Nix

To include the Litrepl Vim plugin to the Litrepl installation, add
`vim-litrepl-release` to the `vimPlugins` list within your `vim_configurable`
expression.

#### Installing latest versions from source using Pip

Installing Vim plugin requires hand-copying
`./vim/plugin/litrepl.vim` and `./vim/plugin/litrepl_extras.vim` to the `~/.vim`
config folder.

### Basic execution


The main Vim command for code section evaluation is `:LEval`. By default, it
executes the section at the cursor. To execute all sections in a document, use
`:LEval all`.


#### Selecting Sections for Execution


The Vim command `:LEval` accepts `eval-section` syntax with the following
additions:

* `@` symbol gets replaced with the `L:C` formatted cursor position
* Words `all`, `above`, and `below` get replaced by the corresponding ranges,
  relative to the current cursor position.

#### Managing Interpreter Sessions

Interpreter sessions could be managed from Vim using the `:LStart CLASS`,
`:LStop [CLASS]`, and `:LRestart [CLASS]` commands which gets directed to their
`start`, `stop` and `restart` CLI versions.

Vim command `:LStatus` corresponds to the `litrepl status` CLI command. The
status message gets printed into the newly-opened Vim buffer. No `CLASS`
argument is currently supported.


#### Asynchronous Processing

The `:LEval` command aims at synchronous execution. For convenience, Vim plugin
defines the `:LEvalAsync` that has 0.5-second initial execution timeout.


The `:LInterrupt` command is equivalent to `litrepl interrupt` CLI command.


Vim plugin also provides the `:LEvalMon` command, which facilitates continuous
code evaluation with no delay. Interrupting this with Ctrl+C will make Litrepl
return control to the editor, leaving the evaluation ongoing in the background.


#### Attaching Interpreter Sessions


The equivalent Vim commands are `:LRepl [CLASS]` or `:LTerm [CLASS]`. Both
commands open Vim terminal window.


