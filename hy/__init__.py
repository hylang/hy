__appname__ = 'hy'
try:
    from hy.version import __version__
except ImportError:
    __version__ = 'unknown'


from hy.models import HyExpression, HyInteger, HyKeyword, HyComplex, HyString, HyBytes, HySymbol, HyFloat, HyDict, HyList, HySet, HyCons  # NOQA


import hy.importer  # NOQA
# we import for side-effects.
