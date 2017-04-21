#!/usr/bin/env python
# Copyright (c) 2012, 2013 Paul Tagliamonte <paultag@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

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
        postpone_filenames = ('macros.hy')
        import_modules_later = []
        for dirpath, _, filenames in os.walk("hy"):
            for filename in filenames:
                if filename.endswith(".hy"):
                    module_to_import = dirpath.replace(
                        "/", ".") + "." + filename[:-len(".hy")]
                    if filename in postpone_filenames:
                        import_modules_later.append(module_to_import)
                        continue
                    importlib.import_module(module_to_import)

        for iml in import_modules_later:
            importlib.import_module(iml)
        install.run(self)

install_requires = ['rply>=0.7.0', 'astor>=0.5', 'clint>=0.4']
if sys.version_info[:2] < (2, 7):
    install_requires.append('argparse>=1.2.1')
    install_requires.append('importlib>=1.0.2')
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
        "Programming Language :: Python :: 2.6",
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
