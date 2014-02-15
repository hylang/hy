# -*- encoding: utf-8 -*-
#
# Decorator for defmulti
#
# Copyright (c) 2014 Morten Linderud <mcfoxax@gmail.com>
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from collections import defaultdict


class MultiDispatch(object):
    _fns = defaultdict(dict)

    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__
        if fn.__name__ not in self._fns[fn.__module__].keys():
            self._fns[fn.__module__][fn.__name__] = {}
        values = fn.__code__.co_varnames
        self._fns[fn.__module__][fn.__name__][values] = fn

    def is_fn(self, v, args, kwargs):
        """Compare the given (checked fn) too the called fn"""
        com = list(args) + list(kwargs.keys())
        if len(com) == len(v):
            return all([kw in com for kw in kwargs.keys()])
        return False

    def __call__(self, *args, **kwargs):
        for i, fn in self._fns[self.fn.__module__][self.fn.__name__].items():
            if self.is_fn(i, args, kwargs):
                return fn(*args, **kwargs)
        raise TypeError("No matching functions with this signature!")
