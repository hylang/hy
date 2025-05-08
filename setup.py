#!/usr/bin/env python

# Set both `setup_requires` and `install_requires` with our
# dependencies, since we need to compile Hy files during setup. And
# put this as the first statement in the file so it's easy to parse
# out without executing the file.
requires = [
    "funcparserlib ~= 1.0",
]

import os

from setuptools import find_packages, setup
from setuptools.command.install import install

os.chdir(os.path.split(os.path.abspath(__file__))[0])

PKG = "hy"

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

setup(
    name=PKG,
    version='1.1.0',
    setup_requires=["wheel"] + requires,
    install_requires=requires,
    python_requires=">= 3.9, < 3.15",
    entry_points={
        "console_scripts": [
            "hy = hy.cmdline:hy_main",
            "hyc = hy.cmdline:hyc_main",
            "hy2py = hy.cmdline:hy2py_main"
        ]
    },
    packages=find_packages(exclude=["tests*"]),
    package_data={
        "": ["*.hy"],
    },
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description="A Lisp dialect embedded in Python",
    license="Expat",
    url="http://hylang.org/",
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: DFSG approved",
        "License :: OSI Approved :: MIT License",  # Really "Expat". Ugh.
        "Operating System :: OS Independent",
        "Programming Language :: Hy",
        "Programming Language :: Lisp",
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: WebAssembly :: Emscripten",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries",
    ],
    project_urls={
        "Documentation": "http://hylang.org/hy/doc",
        "Source": "https://github.com/hylang/hy",
    },
    cmdclass={
        "install": install,
    },
)
