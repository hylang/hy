# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from __future__ import absolute_import

import inspect

try:
    # Check if we have the newer inspect.signature available.
    # Otherwise fallback to the legacy getargspec.
    inspect.signature  # noqa
except AttributeError:
    def has_kwargs(fn):
        argspec = inspect.getargspec(fn)
        return argspec.keywords is not None

    def format_args(fn):
        argspec = inspect.getargspec(fn)
        return inspect.formatargspec(*argspec)

else:
    def has_kwargs(fn):
        parameters = inspect.signature(fn).parameters
        return any(param.kind == param.VAR_KEYWORD
                   for param in parameters.values())

    def format_args(fn):
        return str(inspect.signature(fn))
