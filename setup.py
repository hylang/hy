#!/usr/bin/env python
# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import glob
import importlib
import inspect
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.install import install
import fastentrypoints   # Monkey-patches setuptools.

from get_version import __version__

os.chdir(os.path.split(os.path.abspath(__file__))[0])

PKG = "hy"

long_description = """Hy is a Python <--> Lisp layer. It helps
make things work nicer, and lets Python and the Hy lisp variant play
nice together. """

class Install(install):
    def __compile_hy_bytecode(self):
        for path in sorted(glob.iglob('hy/**.hy', recursive=True)):
            importlib.util.cache_from_source(path, optimize=self.optimize)

    def run(self):
        # Don't bother messing around with deps if they wouldn't be installed anyway.
        # Code is based on setuptools's install.py.
        if not (self.old_and_unmanageable or self.single_version_externally_managed
                or not self._called_from_setup(inspect.currentframe())):
            easy_install = self.distribution.get_command_class('easy_install')

            cmd = easy_install(
                self.distribution, args="x", root=self.root, record=self.record,
            )
            cmd.ensure_finalized()
            cmd.always_copy_from = '.'
            cmd.package_index.scan(glob.glob('*.egg'))

            cmd.args = self.distribution.install_requires

            # Avoid deprecation warnings on new setuptools versions.
            if 'show_deprecation' in inspect.signature(cmd.run).parameters:
                cmd.run(show_deprecation=False)
            else:
                cmd.run()

            # Make sure any new packages get picked up.
            import site
            importlib.reload(site)
            importlib.invalidate_caches()

        self.__compile_hy_bytecode()

        # The deps won't be reinstalled because of:
        # https://github.com/pypa/setuptools/issues/456
        return install.run(self)

install_requires = [
    'rply>=0.7.7',
    'astor>=0.8',
    'funcparserlib>=0.3.6',
    'colorama']
if os.name == 'nt':
    install_requires.append('pyreadline>=2.1')

setup(
    name=PKG,
    version=__version__,
    install_requires=install_requires,
    cmdclass=dict(install=Install),
    entry_points={
        'console_scripts': [
            'hy = hy.cmdline:hy_main',
            'hy3 = hy.cmdline:hy_main',
            'hyc = hy.cmdline:hyc_main',
            'hyc3 = hy.cmdline:hyc_main',
            'hy2py = hy.cmdline:hy2py_main',
            'hy2py3 = hy.cmdline:hy2py_main',
        ]
    },
    packages=find_packages(exclude=['tests*']),
    package_data={
        'hy.contrib': ['*.hy', '__pycache__/*'],
        'hy.core': ['*.hy', '__pycache__/*'],
        'hy.extra': ['*.hy', '__pycache__/*'],
    },
    data_files=[
        ('get_version', ['get_version.py'])
    ],
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description='Lisp and Python love each other.',
    license="Expat",
    url="http://hylang.org/",
    platforms=['any'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: DFSG approved",
        "License :: OSI Approved :: MIT License",  # Really "Expat". Ugh.
        "Operating System :: OS Independent",
        "Programming Language :: Lisp",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ]
)
