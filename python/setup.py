from setuptools import setup, find_packages
from distutils.spawn import find_executable

setup(
  name="litrepl",
  zip_safe=False, # https://mypy.readthedocs.io/en/latest/installed_packages.html
  package_dir={'':'.'},
  packages=find_packages(where='.'),
  install_requires=['lark'],
  scripts=['litrepl.py'],
  python_requires='>=3.6',
)

