#! /usr/bin/env python

''' Setup script for python-entrouvert
'''

from setuptools import setup, find_packages
from setuptools.command.install_lib import install_lib as _install_lib
from distutils.command.build import build as _build
from distutils.command.sdist import sdist  as _sdist
from distutils.cmd import Command

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
        for path in ['entrouvert/djommon/']:
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

def get_version():
    import glob
    import re
    import os

    version = None
    for d in glob.glob('*'):
        if not os.path.isdir(d):
            continue
        module_file = os.path.join(d, '__init__.py')
        if not os.path.exists(module_file):
            continue
        for v in re.findall("""__version__ *= *['"](.*)['"]""",
                open(module_file).read()):
            assert version is None
            version = v
        if version:
            break
    assert version is not None
    if os.path.exists('.git'):
        import subprocess
        p = subprocess.Popen(['git','describe','--dirty','--match=v*'],
                stdout=subprocess.PIPE)
        result = p.communicate()[0]
        assert p.returncode == 0, 'git returned non-zero'
        new_version = result.split()[0][1:]
        assert new_version.split('-')[0] == version, '__version__ must match the last git annotated tag'
        version = new_version.replace('-', '.')
    return version


setup(name="entrouvert",
      version=get_version(),
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
      scripts=('tools/check-git2python-packaging.sh',),
      install_requires=[],
      setup_requires=['nose>=0.11.4'],
      dependency_links=[],
      cmdclass={'build': build, 'install_lib': install_lib,
          'compile_translations': compile_translations,
          'sdist': sdist},
)
