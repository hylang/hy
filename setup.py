#!/usr/bin/env python
# Copyright (c) 2012 Paul Tagliamonte <paultag@debian.org>
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


from hy import __appname__, __version__
from setuptools import setup


long_description = open('README.md', 'r').read()


setup(
    name=__appname__,
    version=__version__,
    scripts=[
        'bin/hytest'
    ],
    packages=[
        'hy',
        'hy.lex',
        'hy.models',
        'hy.compilers',
    ],
    author="Paul Tagliamonte",
    author_email="tag@pault.ag",
    long_description=long_description,
    description='Lisp and Python love each other.',
    license="Expat",
    url="http://hy.pault.ag/",
    platforms=['any']
)
