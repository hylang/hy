#!/usr/bin/env python

import os

import fastentrypoints  # Monkey-patches setuptools.
from get_version import __version__
from setuptools import find_packages, setup

os.chdir(os.path.split(os.path.abspath(__file__))[0])

PKG = "hy"

long_description = """Hy is a Python <--> Lisp layer. It helps
make things work nicer, and lets Python and the Hy lisp variant play
nice together. """

setup(
    name=PKG,
    version=__version__,
    install_requires=[
        "rply>=0.7.7",
        "funcparserlib>=1.0.0a0",
        "colorama",
        'astor>=0.8 ; python_version < "3.9"',
    ],
    python_requires=">= 3.7, < 3.11",
    entry_points={
        "console_scripts": [
            "hy = hy.cmdline:hy_main",
            "hy3 = hy.cmdline:hy_main",
            "hyc = hy.cmdline:hyc_main",
            "hyc3 = hy.cmdline:hyc_main",
            "hy2py = hy.cmdline:hy2py_main",
            "hy2py3 = hy.cmdline:hy2py_main",
        ]
    },
    packages=find_packages(exclude=["tests*"]),
    package_data={
        "hy": ["*.hy", "__pycache__/*"],
        "hy.contrib": ["*.hy", "__pycache__/*"],
        "hy.core": ["*.hy", "__pycache__/*"],
        "hy.extra": ["*.hy", "__pycache__/*"],
    },
    data_files=[("get_version", ["get_version.py"])],
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description="Lisp and Python love each other.",
    license="Expat",
    url="http://hylang.org/",
    platforms=["any"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: DFSG approved",
        "License :: OSI Approved :: MIT License",  # Really "Expat". Ugh.
        "Operating System :: OS Independent",
        "Programming Language :: Lisp",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ],
    project_urls={
        "Documentation": "https://docs.hylang.org/",
        "Source": "https://github.com/hylang/hy",
    },
)
