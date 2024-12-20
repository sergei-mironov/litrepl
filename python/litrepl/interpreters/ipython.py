import re
from os import system
from os.path import join, abspath

from ..utils import fillspaces, runsocat
from ..types import LitreplArgs, EvalState, Interpreter

DEBUG:bool=False

PATTERN_PYTHON_1=('3256748426384\n',)*2
PATTERN_PYTHON_2=('325674801010\n',)*2

class IPythonInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    assert 'ipython' in interpreter.lower()
    cfg=join(abspath(fns.wd), 'litrepl_ipython_config.py')
    log=f"--logfile={join(fns.wd, '_ipython.log')}" if DEBUG else ""
    with open(cfg,'w') as f:
      f.write(
        'import sys\n'
        # See https://github.com/ipython/ipython/issues/14246
        'sys.stdout.reconfigure(line_buffering=True)\n'
        'from IPython.terminal.prompts import Prompts, Token\n'
        'class EmptyPrompts(Prompts):\n'
        '  def in_prompt_tokens(self):\n'
        '    return [(Token.Prompt, "")]\n'
        '  def continuation_prompt_tokens(self, width=None):\n'
        '    return [(Token.Prompt, "") ]\n'
        '  def rewrite_prompt_tokens(self):\n'
        '    return []\n'
        '  def out_prompt_tokens(self):\n'
        '    return []\n'
        'c.TerminalInteractiveShell.prompts_class = EmptyPrompts\n'
        'c.TerminalInteractiveShell.separate_in = ""\n'
        'c.TerminalInteractiveShell.separate_out = ""\n'
      )
    ret=system(
      f"exec {interpreter} --config={cfg} --colors=NoColor {log} -i "
      f"<'{fns.inp}' >'{fns.outp}' 2>&1"
    )
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write(
      '\nimport signal\n'
      'def _handler(signum,frame):\n'
      '  raise KeyboardInterrupt()\n\n'
      '_=signal.signal(signal.SIGINT,_handler)\n'
    )
    if a.exception_exitcode is not None:
      finp.write(
        'import IPython; import os\n'
        'def _exithandler(*args, **kwargs):\n'
        f'  os._exit({int(a.exception_exitcode)})\n\n'
        'IPython.get_ipython().set_custom_exc((Exception,), _exithandler)\n'
      )
  def patterns(self):
    return PATTERN_PYTHON_1,PATTERN_PYTHON_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    # A workaround for https://github.com/ipython/ipython/issues/13622
    r=re.compile('ERROR! Session/line number was not unique in database. '
                 'History logging moved to new session [0-9]+\\n')
    return re.sub(r,'',text)
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    # IPython seems to not echo the terminating cpaste pattern into the output
    # which is good.
    paste_pattern='12341234213423'
    return (f'\n%cpaste -q -s {paste_pattern}\n{code}\n{paste_pattern}\n')
  def run_repl(self, a:LitreplArgs):
    runsocat(self.fns)
