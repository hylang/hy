#!/usr/bin/env python

import os

import fastentrypoints  # Monkey-patches setuptools.
from get_version import __version__
from setuptools import find_packages, setup
from setuptools.command.install import install

os.chdir(os.path.split(os.path.abspath(__file__))[0])

PKG = "dasy-hy"

long_description = """Hy is a Lisp dialect that's embedded in Python.
Since Hy transforms its Lisp code into Python abstract syntax tree (AST)
objects, you have the whole beautiful world of Python at your fingertips,
in Lisp form."""


class install(install):
    def run(self):
        super().run()
        import py_compile

        import hy  # for compile hooks

        for path in set(self.get_outputs()):
            if path.endswith(".hy"):
                py_compile.compile(
                    path,
                    invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH,
                )


# both setup_requires and install_requires
# since we need to compile .hy files during setup
requires = [
    "funcparserlib ~= 1.0",
    "colorama",
    'astor>=0.8 ; python_version < "3.9"',
]

setup(
    name=PKG,
    version="0.24.2",
    setup_requires=["wheel"] + requires,
    install_requires=requires,
    python_requires=">= 3.7, < 3.12",
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
        "": ["*.hy"],
    },
    data_files=[("get_version", ["get_version.py"])],
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description="A Lisp dialect embedded in Python",
    license="Expat",
    url="http://github.com/z80dev/hy",
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
        "Source": "https://github.com/z80dev/hy",
    },
    cmdclass={
        "install": install,
    },
)
