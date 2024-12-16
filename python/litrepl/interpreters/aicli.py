import re
from os import system
from os.path import join
from copy import copy

from ..types import Iterable, LitreplArgs, EvalState, Interpreter, SECVAR_RE
from ..eval import eval_code_raw
from ..utils import fillspaces, runsocat, SOCAT_HINT

PATTERN_GPT4ALLCLI_1=('/echo 1121312\n', '1121312\n')
PATTERN_GPT4ALLCLI_2=('/echo 8893223\n', '8893223\n')

def secvar_matches(code:str)->Iterable[tuple[str,int]]:
  for secvar in re.findall(SECVAR_RE,code):
    secvar=[m for m in secvar if len(m)>0][0]
    idx=int(''.join([c for c in secvar if c.isdigit()]))
    yield str(secvar),idx

class AicliInterpreter(Interpreter):
  endcmd="/ask"
  def run_child(self,interpreter)->int:
    fns=self.fns
    ret=system(
      f"exec {interpreter} "
      f"<'{fns.inp}' >'{fns.outp}' 2>&1"
    )
    return ret
  def setup_child(self, a, finp, foutp)->None:
    finp.write("/set terminal prompt \"\"\n")
    finp.write("/set terminal verbosity 2\n")
    finp.write("/echo ready\n")
  def patterns(self):
    return PATTERN_GPT4ALLCLI_1,PATTERN_GPT4ALLCLI_2
  def result_postprocess(self, a:LitreplArgs, text:str) -> str:
    text=text.strip()
    if text.endswith(self.endcmd):
      text=text[:-len(self.endcmd)].strip()
    return text+"\n"
  def code_preprocess(self, a:LitreplArgs, es:EvalState, code:str) -> str:
    for secvar,ref in secvar_matches(copy(code)):
      if secvar[0]=='^':
        assert ref>=1, "Above reference must be greater or equal one"
        absref=es.nsec-ref
      elif secvar[0]=='v':
        assert ref>=1, "Below reference must be greater or equal one"
        absref=es.nsec+ref
      elif secvar[0]=='>':
        absref=ref
      else:
        raise ValueError("Invalid section variable {secvar}")
      code=code.replace(
        secvar,
        es.sres.get(
          absref,
          es.sr.preproc.results.get(absref,f'<invalid reference to section {absref}>').strip()
        )
      )
    return code + f"{self.endcmd}\n"
  def run_repl(self, a:LitreplArgs):
    rr,_=eval_code_raw(self,f"/set terminal prompt \">>> \"\n\n",
                  float('inf'),float('inf'),True)
    assert not rr.timeout, "Setting non-empty prompt did not happen fast"
    runsocat(self.fns, hint=SOCAT_HINT.replace('NO PROMPTS, ','')+'>>> ')
    rr,_=eval_code_raw(self,f"/set terminal prompt \"\"\n",
                  float('inf'),float('inf'),True)
    assert not rr.timeout, "Setting empty prompt did not happen fast"

