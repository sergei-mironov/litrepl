from logging import getLogger
logger=getLogger(__name__)
info=logger.info
warning=logger.warning

from litrepl.base import *

try:
  from litrepl.version import __version__
except ImportError:
  try:
    from setuptools_scm import get_version
    from os.path import join
    __version__ = get_version(root=join('..','..'), relative_to=__file__)
  except Exception:
    warning("LitREPL failed to read its version.")
    __version__ = None
