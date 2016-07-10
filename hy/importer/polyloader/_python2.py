import io
import os
import os.path
import sys
import imp
import types
import pkgutil
from collections import namedtuple


SEP = os.sep
EXS = os.extsep
FLS = [('%s' + SEP + '__init__' + EXS + '%s', True), 
       ('%s' + EXS + '%s', False)]

Loader = namedtuple('Loader', 'suffix compiler')

class PolyLoader():
    def __init__(self, fullname, path, is_pkg):
        self.fullname = fullname
        self.path = path
        self.is_package = is_pkg

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        if fullname != self.fullname:
            raise ImportError("Load confusion: %s vs %s." % (fullname, self.fullname))

        matches = [loader for loader in PolyFinder._loader_handlers
                   if self.path.endswith(loader.suffix)]

        if len(matches) == 0:
            raise ImportError("%s is not a recognized module?" % fullname)

        if len(matches) > 1:
            raise ImportError("Multiple possible resolutions for %s: %s" % (
                fullname, ', '.join([loader.suffix for loader in matches])))

        compiler = matches[0].compiler
        with io.FileIO(self.path, 'r') as file:
            source_text = file.read()

        code = compiler(source_text, self.path, fullname)

        module = types.ModuleType(fullname)
        module.__file__ = self.path
        module.__name__ = fullname
        module.__package__ = '.'.join(fullname.split('.')[:-1])

        if self.is_package:
            module.__path__ = [os.path.dirname(module.__file__)]
            module.__package__ = fullname

        exec(code, module.__dict__)
        sys.modules[fullname] = module
        return module


# PolyFinder is an implementation of the Finder class from Python 2.7,
# with embellishments gleefully copied from Python 3.4.  It supports
# all the same functionality for non-.py sourcefiles with the added
# benefit of falling back to Python's default behavior.

# Polyfinder is instantiated by _polyloader_pathhook()

class PolyFinder(object):
    _loader_handlers = []
    _installed = False

    def __init__(self, path=None):
        self.path = path or '.'

    def _pl_find_on_path(self, fullname, path=None):
        subname = fullname.split(".")[-1]
        if self.path is None and subname != fullname:
            return None

        path = os.path.realpath(self.path)
        for (fp, ispkg) in FLS:
            for loader in self._loader_handlers:
                composed_path = fp % (('%s' + SEP + '%s') % (path, subname), loader.suffix)
                if os.path.isdir(composed_path):
                    raise IOError("Invalid: Directory name ends in recognized suffix")
                if os.path.isfile(composed_path):
                    return PolyLoader(fullname, composed_path, ispkg)

        # Fall back onto Python's own methods.
        try:
            file, filename, etc = imp.find_module(subname, [path])
        except ImportError as e:
            return None
        return pkgutil.ImpLoader(fullname, file, filename, etc)

    def find_module(self, fullname, path=None):
        return self._pl_find_on_path(fullname)

    @classmethod
    def _install(cls, compiler, suffixes):
        if isinstance(suffixes, basestring):
            suffixes = [suffixes]
        suffixes = set(suffixes)
        overlap = suffixes.intersection(set([suf[0] for suf in imp.get_suffixes()]))
        if overlap:
            raise RuntimeError("Override of native Python extensions is not permitted.")
        overlap = suffixes.intersection(
            set([loader.suffix for loader in cls._loader_handlers]))
        if overlap:
            # Fail silently
            return
        cls._loader_handlers += [Loader(suf, compiler) for suf in suffixes]

    @classmethod
    def getmodulename(cls, path):
        filename = os.path.basename(path)
        suffixes = ([(-len(suf[0]), suf[0]) for suf in imp.get_suffixes()] +
                    [(-(len(suf[0]) + 1), EXS + suf[0]) for suf in cls._loader_handlers])
        suffixes.sort()
        for neglen, suffix in suffixes:
            if filename[neglen:] == suffix:
                return filename[:neglen]
        return None

    def iter_modules(self, prefix=''):
        if self.path is None or not os.path.isdir(self.path):
            return

        yielded = {}

        try:
            filenames = os.listdir(self.path)
        except OSError:
            # ignore unreadable directories like import does
            filenames = []
        filenames.sort()
        for fn in filenames:
            modname = self.getmodulename(fn)
            if modname == '__init__' or modname in yielded:
                continue

            path = os.path.join(self.path, fn)
            ispkg = False

            if not modname and os.path.isdir(path) and '.' not in fn:
                modname = fn
                try:
                    dircontents = os.listdir(path)
                except OSError:
                    # ignore unreadable directories like import does
                    dircontents = []
                for fn in dircontents:
                    subname = self.getmodulename(fn)
                    if subname == '__init__':
                        ispkg = True
                        break
                else:
                    continue    # not a package

            if modname and '.' not in modname:
                yielded[modname] = 1
                yield prefix + modname, ispkg


def _polyloader_pathhook(path):
    if not os.path.isdir(path):
        raise ImportError('Only directories are supported: %s' % path)
    return PolyFinder(path)


def install(compiler, suffixes):
    if not PolyFinder._installed:
        sys.path_hooks.append(_polyloader_pathhook)
        PolyFinder._installed = True
    PolyFinder._install(compiler, suffixes)


def reset():
    PolyFinder._loader_handlers = []
    PolyFinder._installed = False
