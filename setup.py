from setuptools import setup, find_packages
from os.path import join, dirname
from os import environ
from logging import getLogger
from typing import Optional
logger=getLogger(__name__)
warning=logger.warning

LITREPL_REVISION:Optional[str]
try:
  LITREPL_REVISION=environ["LITREPL_REVISION"]
except Exception:
  warning("Couldn't read LITREPL_REVISION, trying `git rev-parse`")
  try:
    from subprocess import check_output
    import sys
    LITREPL_REVISION=check_output(['git', 'rev-parse', 'HEAD'],
                                  cwd=dirname(__file__)).decode().strip()
  except Exception:
    warning("Couldn't use `git rev-parse`, no revision metadata will be set")
    LITREPL_REVISION=None


LITREPL_SEMVER:Optional[str]
try:
  LITREPL_SEMVER=open(join(dirname(__file__),'semver.txt')).read().strip()
except Exception:
  warning("Couldn't read 'version.txt', no metadata will be set")
  LITREPL_SEMVER=None


if LITREPL_REVISION:
  with open(join('python','litrepl','revision.py'), 'w') as f:
    f.write("# AUTOGENERATED by setup.exe!\n")
    f.write(f"__revision__ = '{LITREPL_REVISION}'\n")

if LITREPL_SEMVER:
  with open(join('python','litrepl','semver.py'), 'w') as f:
    f.write("# AUTOGENERATED by setup.exe!\n")
    f.write(f"__semver__ = '{LITREPL_SEMVER}'\n")

setup(
  name="litrepl",
  zip_safe=False, # https://mypy.readthedocs.io/en/latest/installed_packages.html
  version=LITREPL_SEMVER if LITREPL_SEMVER else "999",
  package_dir={'':'python'},
  packages=find_packages(where='python'),
  install_requires=['lark', 'psutil'],
  scripts=['./python/bin/litrepl'],
  python_requires='>=3.6',
  author="Sergei Mironov",
  author_email="grrwlf@gmail.com",
  description="LitREPL is a macroprocessing Python library for Litrate "\
              "programming and code execution.",
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: POSIX :: Linux",
    "Topic :: Software Development :: Build Tools",
    "Intended Audience :: Developers",
    "Development Status :: 3 - Alpha",
  ],
)

