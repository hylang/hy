__appname__ = 'hy'
try:
    from hy.version import __version__
except ImportError:
    __version__ = 'unknown'


from hy.models import HyExpression, HyInteger, HyKeyword, HyComplex, HyString, HyBytes, HySymbol, HyFloat, HyDict, HyList, HySet  # NOQA


import hy.importer  # NOQA
# we import for side-effects.


from hy.core.language import read, read_str, mangle, unmangle  # NOQA
from hy.importer import hy_eval as eval  # NOQA


def interact(banner=None, readfunc=None, local=None, exitmsg=None):
    from hy.cmdline import HyREPL
    console = HyREPL(locals=local)
    if readfunc is not None:
        console.raw_input = readfunc
    else:
        try:
            import readline
        except ImportError:
            pass
    console.interact(banner, exitmsg)
