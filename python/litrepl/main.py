import litrepl
from litrepl import *
from litrepl import __version__, eval_section_
from os import chdir, getcwd, environ
from subprocess import check_output, DEVNULL, CalledProcessError
from argparse import ArgumentParser, HelpFormatter
from tempfile import mkdtemp
from functools import partial

LOCSHELP='(N|$|N..N)[,(...)] where N is either: number,$,ROW:COL'

def make_wide(formatter, w=180, h=28):
  """Return a wider HelpFormatter, if possible.
  Source: https://stackoverflow.com/a/5464440
  beware: "Only the name of this class is considered a public API.
  """
  try:
    kwargs={'max_help_position':30,'width':78}
    # formatter(None, **kwargs)
    return lambda prog: formatter(prog, **kwargs)
  except TypeError:
    warnings.warn("argparse help formatter failed, falling back.")
    return formatter

def _with_type(p, default=None, allow_all=False):
  defhint=f"Default is \"{default}\"" if default else ''
  p.add_argument(
    'type',metavar='CLASS',default=default,
    help=dedent(f'''Interpreter class: python|ai|sh{'|all' if allow_all else ''}.
    {defhint}'''),nargs='?' if default is not None else None
  )
  return p

def make_parser():
  ap=ArgumentParser(prog='litrepl',
                    formatter_class=make_wide(HelpFormatter))
  ap.add_argument('-v','--version',action='version',version=__version__ or '?',
    help='Print version.')
  ap.add_argument('--filetype',metavar='STR',default='auto',
    help='Specify the type of input formatting (markdown|[la]tex|auto).')
  ap.add_argument('--python-markers',metavar='STR[,STR]',
    default=environ.get('LITREPL_PYTHON_MARKERS','python'),
    help=dedent('''TODO'''))
  ap.add_argument('--ai-markers',metavar='STR[,STR]',
    default=environ.get('LITREPL_AI_MARKERS','ai'),
    help=dedent('''TODO'''))
  ap.add_argument('--sh-markers',metavar='STR[,STR]',
    default=environ.get('LITREPL_SH_MARERS','sh,bash'),
    help=dedent('''TODO'''))
  ap.add_argument('--python-interpreter',metavar='EXE',
    default=environ.get('LITREPL_PYTHON_INTERPRETER','auto'),
    help=dedent('''Python interpreter command line, or `auto`. Defaults to the
    LITREPL_PYTHON_INTERPRETER environment variable if set, otherwise "auto".
    Litrepl determines "python" or "ipython" type according to the value.'''))
  ap.add_argument('--ai-interpreter',metavar='EXE',
    default=environ.get('LITREPL_AI_INTERPRETER','auto'),
    help=dedent('''`aicli` interpreter command line or `auto`. Defaults to the
    LITREPL_AI_INTERPRETER environment variable if set, otherwise "auto".'''))
  ap.add_argument('--sh-interpreter',metavar='EXE',
    default=environ.get('LITREPL_SH_INTERPRETER','auto'),
    help=dedent('''Shell interpreter command line or `auto`. Defaults to the
    LITREPL_SH_INTERPRETER environment variable if set, otherwise "auto".'''))
  ap.add_argument('--python-auxdir',type=str,metavar='DIR',
    default=environ.get('LITREPL_PYTHON_AUXDIR'),
    help=dedent('''This directory stores Python interpreter pipes. It defaults
    to LITREPL_PYTHON_AUXDIR if set; otherwise, it's created in the system's
    temporary directory, named after the current working directory.'''))
  ap.add_argument('--ai-auxdir',type=str,metavar='DIR',
    default=environ.get('LITREPL_AI_AUXDIR'),
    help=dedent('''This directory stores AI interpreter pipes. It defaults to
    LITREPL_AI_AUXDIR if set; otherwise, it's created in the system's temporary
    directory, named after the current working directory.'''))
  ap.add_argument('--sh-auxdir',type=str,metavar='DIR',
    default=environ.get('LITREPL_SH_AUXDIR'),
    help=dedent('''This directory stores AI interpreter pipes. It defaults to
    LITREPL_SH_AUXDIR if set; otherwise, it's created in the system's temporary
    directory, named after the current working directory.'''))
  ap.add_argument('--timeout',type=str,metavar='F[,F]',default='inf',
    help=dedent('''Timeouts for initial evaluation and for pending checks, in
    seconds. If the latter is omitted, it is considered to be equal to the
    former one.'''))
  ap.add_argument('--propagate-sigint',action='store_true',
    help=dedent('''If set, litrepl will catch and resend SIGINT signals to the
    running interpreter. Otherwise it will just terminate itself leaving the
    interpreter as-is.'''))
  ap.add_argument('-d','--debug',type=int,metavar='INT',default=0,
    help="Enable (a lot of) debug messages.")
  ap.add_argument('--verbose',action='store_true',
    help='Be more verbose (used in status).')
  ap.add_argument('-C','--workdir',type=str,metavar='DIR',
    default=environ.get('LITREPL_WORKDIR',None),
    help=dedent('''Set the working directory before execution. By default, it
    uses LITREPL_WORKDIR if set, otherwise remains the current directory. This
    affects the directory of a new interpreter and the --<interpreter>-auxdir
    option.'''))
  ap.add_argument('--pending-exitcode',type=str,metavar='INT',default=None,
    help=dedent('''Return this error code if whenever a section hits timeout.'''))
  ap.add_argument('--irreproducible-exitcode',type=str,metavar='INT',default=None,
    help=dedent('''Return this error code if a section outputs a different
    result than the one that is already present in the document.'''))
  ap.add_argument('--exception-exitcode',type=str,metavar='INT',default=None,
    help=dedent('''Return this error code at exception, if any. Note: this
    option might not be defined for some interpreters. It takes affect only for
    newly-started interpreters.'''))
  ap.add_argument('--foreground',action='store_true',
    help=dedent('''Start a separate session and stop it when the evaluation is
    done. All --*-auxdir settings are ignored in this mode.'''))
  ap.add_argument('--map-cursor',type=str,metavar='LINE:COL:FILE',default=None,
    help=dedent('''Calculate the new position of a cursor at LINE:COL and write
    it to FILE.'''))
  ap.add_argument('--result-textwidth',type=str,metavar='NUM',default=None,
    help=dedent('''Wrap result lines longer than NUM symbols.'''))
  sps=ap.add_subparsers(dest='command',help='Commands to execute')
  sstart=_with_type(sps.add_parser('start',
    help='Start the background interpreter.'))
  _with_type(sps.add_parser('stop',
    help='Stop the background interpreters.'),allow_all=True,default='all')
  _with_type(sps.add_parser('restart',
    help='Restart the background interpreters.'),allow_all=True,default='all')
  sstatus=_with_type(sps.add_parser('status',
    help='Print background interpreter\'s status.'),allow_all=True,default='all')
  sstatus.add_argument('--tty',action='store_true',
    help='Read intput document from stdin (required to get per-section status).')
  sps.add_parser('parse',
    help='Parse the input file without futher processing (diagnostics).')
  sps.add_parser('parse-print',
    help=dedent('''Parse and print the input file back (diagnostics).'''))
  evalsec=sps.add_parser('eval-sections',
    help=dedent('''Parse stdin, evaluate the sepcified sections (by default - all
    available sections), print the resulting file to stdout.'''))
  evalsec.add_argument('locs',type=str,metavar='LOCS',default='0..$',help=LOCSHELP,nargs='?')
  _with_type(sps.add_parser('eval-code', help='Evaluate the code snippet.'))
  _with_type(sps.add_parser('repl', help='Connect to the background terminal using GNU socat.'))
  interrupt=sps.add_parser('interrupt',
    help='Send SIGINT to the background interpreter.')
  interrupt.add_argument('locs',metavar='LOCS',default='0..$',help=LOCSHELP,nargs='?')
  regexp=sps.add_parser('print-regexp',
    help='Print regexp matching start of code sections for the given file type.')
  regexp.add_argument('format',metavar='STR',default='vim',
    help=dedent('''Regexp format to print: 'vim' or 'lark'. Defaults to 'vim'''),nargs='?')
  regexp.add_argument('--tty',action='store_true',
    help='Read intput document from stdin (required to get per-section status).')
  grammar=sps.add_parser('print-grammar',
    help=dedent('''Print the resulting grammar for the given filetype.'''))
  grammar.add_argument('--tty',action='store_true',
    help='Read intput document from stdin (required to get per-section status).')
  return ap

AP=make_parser()

def main(args=None):
  a=AP.parse_args(args or sys.argv[1:])

  if a.debug>0:
    litrepl.eval.DEBUG=True
    litrepl.base.DEBUG=True
    litrepl.utils.DEBUG=True
    litrepl.interpreters.ipython.DEBUG=True

  timeouts=a.timeout.split(',')
  assert len(timeouts) in {1,2}, f"invalid timeout value {timeouts}"
  a.timeout_initial=float(timeouts[0])
  a.timeout_continue=float(timeouts[1] if len(timeouts)==2 else timeouts[0])

  a.markers={
    SType.SAI:a.ai_markers.split(","),
    SType.SShell:a.sh_markers.split(","),
    SType.SPython:a.python_markers.split(",")
  }
  for st in SType:
    for bm in a.markers[st]:
      st2=bmarker2st(a,bm)
      pdebug(st,bm, f"dis:{isdisabled(a,st)}", '======>',st2)
      assert isdisabled(a,st) or (st2 is not None), (st,bm,st2)

  if a.exception_exitcode:
    a.exception_exitcode=int(a.exception_exitcode)

  if a.pending_exitcode:
    a.pending_exitcode=int(a.pending_exitcode)

  if a.irreproducible_exitcode:
    if (a.timeout_initial,a.timeout_continue)!=(float('inf'),float('inf')):
      raise ValueError(
        f"Setting --irreproducible-exitcode requires setting infinite "
        f"--timeout, not \"{a.timeout_initial},{a.timeout_continue}\""
      )
    a.irreproducible_exitcode=int(a.irreproducible_exitcode)

  if a.result_textwidth:
    a.result_textwidth=int(a.result_textwidth)
    if a.result_textwidth==0:
      a.result_textwidth=None # for vim-compatibility

  if a.map_cursor:
    line,col,output=a.map_cursor.split(":")
    a.map_cursor=(int(line),int(col))
    a.map_cursor_output=output

  if a.workdir:
    chdir(a.workdir)

  if not hasattr(a,'tty'):
    a.tty=False

  ecode=1

  def _foreground_stop(st):
    if a.foreground:
      stop(a,st)

  if a.foreground:
    assert a.command not in {'start','stop','restart','repl','interrupt'}, \
      f"--foreground is not compatible with '{a.command}' command"
    for st in [SType.SPython,SType.SAI,SType.SShell]:
      setattr(a,f"{st2name(st)}_auxdir",
              mkdtemp(prefix=f"litrepl-{st2name(st)}-foreground"))

  if a.command=='start':
    ecode=start(a,name2st(a.type))
    exit(ecode)
  elif a.command=='stop':
    for st in SType:
      if a.type in {st2name(st),"all",None}:
        stop(a,st)
  elif a.command=='restart':
    if a.type in {'all',None}:
      for st in SType:
        if running(a,st):
          restart(a,st)
    else:
      restart(a,name2st(a.type))
  elif a.command=='parse':
    t=parse_(a).tree
    print(t.pretty())
    exit(0)
  elif a.command=='parse-print':
    sr0=SecRec(set(),{})
    ecode=eval_section_(a,parse_(a).tree,sr0)
    exit(0 if ecode is None else ecode)
  elif a.command=='eval-sections':
    t=parse_(a).tree
    nsecs=solve_sloc(a.locs,t)
    ecode=eval_section_(a,t,nsecs)
    exit(0 if ecode is None else ecode)
  elif a.command=='repl':
    st=name2st(a.type)
    with with_parent_finally(partial(_foreground_stop,st)):
      fns=pipenames(a,st)
      if not running(a,st) or a.foreground:
        start(a,st)
      ss=attach(fns,st)
      assert ss is not None, f"Failed to attach to {st2name(st)} interpreter"
      ss.run_repl(a)
      ecode=interpExitCode(fns,undefined=200)
    exit(0 if ecode is None else ecode)
  elif a.command=='interrupt':
    tree=parse_(a).tree
    sr=solve_sloc(a.locs,tree)
    sr.nsecs|=set(sr.preproc.pending.keys())
    ecode=eval_section_(a,tree,sr,interrupt=True)
    exit(ecode)
  elif a.command=='eval-code':
    st=name2st(a.type)
    es=EvalState(SecRec.empty())
    with with_parent_finally(partial(_foreground_stop,st)):
      fns=pipenames(a,st)
      if not running(a,st) or a.foreground:
        start(a,st)
      ss=attach(fns,st)
      assert ss is not None, f"Failed to attach to {st2name(st)} interpreter"
      print(eval_code(a,fns,ss,es,sys.stdin.read()),end='',flush=True)
      ecode=interpExitCode(fns,undefined=200)
    exit(0 if ecode is None else ecode)
  elif a.command=='status':
    t=parse_(a).tree
    if a.foreground:
      st=name2st(a.type)
      with with_parent_finally(partial(_foreground_stop,st)):
        start(a,st)
        ecode=status(a,t,[st],__version__)
      exit(0 if ecode is None else ecode)
    else:
      sts=[]
      for st in SType:
        if a.type in {st2name(st),"all",None}:
          sts.append(st)
      ecode=status(a,t,sts,__version__)
      exit(0 if ecode is None else ecode)
  elif a.command=='print-regexp':
    s=parse_(a).symbols
    regexp=s.codebegin_dict.get(a.format)
    if regexp is None:
      raise ValueError(f"Unsupported regexp format \"{a.format}\"")
    print(regexp)
  elif a.command=='print-grammar':
    g=parse_(a).grammar
    print(g)
  else:
    pstderr(f'Unknown command: {a.command}')
    exit(1)


