from os import system

from ..types import LitreplArgs, EvalState, Interpreter
from ..utils import fillspaces, runsocat

PATTERN_PYTHON_1=('3256748426384\n',)*2
PATTERN_PYTHON_2=('325674801010\n',)*2

class PythonInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    ret=system(
      f"exec {interpreter} -uic 'import sys; sys.ps1=\"\"; sys.ps2=\"\";' "
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
        'import sys; import os\n'
        'def _exceptexithook(type,value,traceback):\n'
        f'  os._exit({a.exception_exitcode})\n\n'
        'sys.excepthook=_exceptexithook\n'
      )
  def patterns(self):
    return PATTERN_PYTHON_1,PATTERN_PYTHON_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    return text
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    return fillspaces(code, '# spaces')
  def run_repl(self, a:LitreplArgs):
    runsocat(self.fns)

