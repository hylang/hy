# colorama's deinit isn't working, probably due to
# https://github.com/tartley/colorama/issues/145
# This is located here to save the original streams before clint gets to them.
# TODO: remove when colorama fixes it.
from sys import stdout as _out, stderr as _err
def colorama_deinit():
    import sys
    sys.stdout, sys.stderr = _out, _err

__appname__ = 'hy'
try:
    from hy.version import __version__
except ImportError:
    __version__ = 'unknown'


from hy.models import HyExpression, HyInteger, HyKeyword, HyComplex, HyString, HyBytes, HySymbol, HyFloat, HyDict, HyList, HySet, HyCons  # NOQA


import hy.importer  # NOQA
# we import for side-effects.


from hy.core.language import read, read_str  # NOQA
from hy.importer import hy_eval as eval  # NOQA
