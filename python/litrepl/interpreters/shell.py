from os import system, setsid, getsid, getpid

from ..types import LitreplArgs, EvalState, Interpreter
from ..utils import fillspaces, runsocat
from ..eval import pdebug

PATTERN_1=('echo 3256748426384\n','3256748426384\n')
PATTERN_2=('echo ASDSADQ231212\n','ASDSADQ231212\n')

class ShellInterpreter(Interpreter):
  def run_child(self,interpreter)->int:
    fns=self.fns
    # before=getsid(0)
    # setsid()
    # after=getsid(0)
    # pdebug(f"SID after {after}")
    cmd=(f"PS1=\"\" PS2=\"\" exec setsid {interpreter} "
         f"<'{fns.inp}' >'{fns.outp}' 2>&1")
    ret=system(cmd)
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write('trap "echo ^C" INT\n')
    pass
  def patterns(self):
    return PATTERN_1,PATTERN_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    return text
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    return code
  def run_repl(self, a:LitreplArgs) -> None:
    runsocat(self.fns)

