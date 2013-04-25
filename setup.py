#! /usr/bin/env python

''' Setup script for python-entrouvert
'''

from setuptools import setup, find_packages
from setuptools.command.install_lib import install_lib as _install_lib
from distutils.command.build import build as _build
from distutils.command.sdist import sdist  as _sdist
from distutils.cmd import Command
import glob

class compile_translations(Command):
    description = 'compile message catalogs to MO files via django compilemessages'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import os
        import sys
        from django.core.management.commands.compilemessages import \
            compile_messages
        for path in []:
            if path.endswith('.py'):
                continue
            curdir = os.getcwd()
            os.chdir(os.path.realpath(path))
            compile_messages(stderr=sys.stderr)
            os.chdir(curdir)

class build(_build):
    sub_commands = [('compile_translations', None)] + _build.sub_commands

class sdist(_sdist):
    sub_commands = [('compile_translations', None)] + _sdist.sub_commands

class install_lib(_install_lib):
    def run(self):
        self.run_command('compile_translations')
        _install_lib.run(self)

setup(name="entrouvert",
      version=1.0,
      license="AGPLv3 or later",
      description="Entr'ouvert tools",
      url="http://dev.entrouvert.org/projects/python-entrouvert/",
      author="Entr'ouvert",
      author_email="info@entrouvert.org",
      maintainer="Benjamin Dauvergne",
      maintainer_email="info@entrouvert.com",
      include_package_data=True,
      package_data={
          '': [
              ]
      },
      packages=find_packages(),
      scripts=(),
      install_requires=[],
      setup_requires=['nose>=1.0'],
      dependency_links=[],
      cmdclass={'build': build, 'install_lib': install_lib,
          'compile_translations': compile_translations,
          'sdist': sdist},
)
