#!/usr/bin/env python
# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import re
import sys
import runpy
import subprocess

from setuptools import find_packages, setup
from setuptools.command.install import install

os.chdir(os.path.split(os.path.abspath(__file__))[0])

PKG = "hy"
VERSIONFILE = os.path.join(PKG, "version.py")
try:
    __version__ = (subprocess.check_output
        (["git", "describe", "--tags", "--dirty"])
        .decode('ASCII').strip()
        .replace('-', '+', 1).replace('-', '.'))
    with open(VERSIONFILE, "wt") as o:
        o.write("__version__ = {!r}\n".format(__version__))
except (subprocess.CalledProcessError, OSError):
    if os.path.exists(VERSIONFILE):
        __version__ = runpy.run_path(VERSIONFILE)['__version__']
    else:
        __version__ = "unknown"

long_description = """Hy is a Python <--> Lisp layer. It helps
make things work nicer, and lets Python and the Hy lisp variant play
nice together. """

class Install(install):
    def run(self):
        # Import each Hy module to ensure it's compiled.
        import os, importlib
        for dirpath, _, filenames in sorted(os.walk("hy")):
            for filename in sorted(filenames):
                if filename.endswith(".hy"):
                    importlib.import_module(
                        dirpath.replace("/", ".").replace("\\", ".") +
                        "." + filename[:-len(".hy")])
        install.run(self)

install_requires = ['rply>=0.7.0', 'astor>=0.5', 'clint>=0.4']
if os.name == 'nt':
    install_requires.append('pyreadline>=2.1')

ver = sys.version_info[0]

setup(
    name=PKG,
    version=__version__,
    install_requires=install_requires,
    cmdclass=dict(install=Install),
    entry_points={
        'console_scripts': [
            'hy = hy.cmdline:hy_main',
            'hy%d = hy.cmdline:hy_main' % ver,
            'hyc = hy.cmdline:hyc_main',
            'hyc%d = hy.cmdline:hyc_main' % ver,
            'hy2py = hy.cmdline:hy2py_main',
            'hy2py%d = hy.cmdline:hy2py_main' % ver,
        ]
    },
    packages=find_packages(exclude=['tests*']),
    package_data={
        'hy.contrib': ['*.hy', '__pycache__/*'],
        'hy.core': ['*.hy', '__pycache__/*'],
        'hy.extra': ['*.hy', '__pycache__/*'],
    },
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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ]
)
