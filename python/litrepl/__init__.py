from typing import Optional
from os.path import join
from logging import getLogger
logger=getLogger(__name__)
info=logger.info
warning=logger.warning

from .types import *
from .utils import *
from .eval import *
from .base import *

# Determine the package version using the following source priorities:
# 1) semver.txt+git 2) semver.txt 3) version.py
__revision__:Optional[str]
try:
  __revision__=environ["LITREPL_REVISION"]
except Exception:
  try:
    from subprocess import check_output, DEVNULL
    __revision__=check_output(['git', 'rev-parse', 'HEAD'],
                            cwd=environ['LITREPL_ROOT'],
                            stderr=DEVNULL).decode().strip()
  except Exception:
    try:
      from litrepl.revision import __revision__ as __rv__
      __revision__=__rv__
    except ImportError:
      __revision__=None


__semver__:Optional[str]
try:
  __semver__=open(join(environ['LITREPL_ROOT'],'semver.txt')).read().strip()
except Exception:
    try:
      from litrepl.semver import __semver__ as __sv__
      __semver__= __sv__
    except ImportError:
      __semver__=None


__version__:Optional[str]
__version__=(__semver__ + (f"+g{__revision__[:7]}" \
                           if __revision__ else "")) if __semver__ else None
