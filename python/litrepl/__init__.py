from logging import getLogger
logger=getLogger(__name__)
info=logger.info
warning=logger.warning

from .types import *
from .eval import *
from .base import *

try:
  from litrepl.version import __version__
except ImportError:
  try:
    from setuptools_scm import get_version
    from os.path import join
    __version__ = get_version(root=join('..','..'), relative_to=__file__)
  except Exception:
    warning("Neither `litrepl/version.py` module was not generated during the "
            "setup, nor the Git metadata is available. Re-install litrepl with "
            "the `setuptools_scm` package available to fix")
    __version__ = None
