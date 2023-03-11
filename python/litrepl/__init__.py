from typing import Optional
from os.path import join
from logging import getLogger
logger=getLogger(__name__)
info=logger.info
warning=logger.warning

from .types import *
from .eval import *
from .base import *

# Determine the package version using the following source priorities:
# 1) version.txt+git 2) version.txt 3) version.py
__version__:Optional[str]
try:
  LITREPL_ROOT=environ['LITREPL_ROOT']
  ver=open(join(LITREPL_ROOT,'version.txt')).read().strip()
  LITREPL_REVISION:Optional[str]
  try:
    from subprocess import check_output
    LITREPL_REVISION=check_output(['git', 'rev-parse', 'HEAD'],
                                  cwd=LITREPL_ROOT).decode().strip()
  except Exception:
    try:
      LITREPL_REVISION=environ["LITREPL_REVISION"]
    except Exception:
      LITREPL_REVISION=None

  rev=f"+g{LITREPL_REVISION[:7]}" if LITREPL_REVISION is not None else ""
  __version__ = f"{ver}{rev}"
except Exception:
  try:
    from litrepl.version import __version__
  except ImportError:
    warning("Neither `litrepl/version.py` module was not generated during the "
            "setup, nor the Git metadata is available. Re-install litrepl with "
            "the `setuptools_scm` package available to fix")
    __version__ = None
