#!/usr/bin/env python

from setuptools import setup

long_description = """This thing does stuff and
things with other things until things looks like other
things.  """

appname = "hy"
version = "0.7.5"

setup(**{
    "name": appname,
    "version": version,
    "packages": [
        'hy',
        'hy.lang',
        'hy.lex',
        'hy.compiler'
    ],
    "author": "Paul Tagliamonte",
    "author_email": "tag@pault.ag",
    "long_description": long_description,
    "description": 'lisp and python love eachother',
    "license": "Expat",
    "url": "http://hy.pault.ag/",
    "platforms": ['any'],
    "scripts": [
        "bin/hython"
    ]
})
