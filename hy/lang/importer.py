# from hy.compiler.modfaker import forge_module
from hy.compiler.ast27 import forge_module

from hy.lex.tokenize import tokenize
import sys
import imp
import os


def _hy_import_file(fd, name):
    m = forge_module(
        name,
        fd,
        tokenize(open(fd, 'r').read())
    )
    return m


class HyFinder(object):
    def is_package(self, fullname):
        dirpath = "/".join(fullname.split("."))
        for pth in sys.path:
            pth = os.path.abspath(pth)
            composed_path = "%s/%s/__init__.hy" % (pth, dirpath)
            if os.path.exists(composed_path):
                return True
        return False

    def find_on_path(self, fullname):
        fls = ["%s/__init__.hy", "%s.hy"]
        dirpath = "/".join(fullname.split("."))

        for pth in sys.path:
            pth = os.path.abspath(pth)
            for fp in fls:
                composed_path = fp % ("%s/%s" % (pth, dirpath))
                if os.path.exists(composed_path):
                    return composed_path


class MetaLoader(HyFinder):
    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        pth = self.find_on_path(fullname)
        if pth is None:
            return

        sys.modules[fullname] = None
        mod = _hy_import_file(pth, fullname)

        ispkg = self.is_package(fullname)

        mod.__file__ = pth
        mod.__loader__ = self

        if ispkg:
            mod.__path__ = []
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]

        sys.modules[fullname] = mod
        return mod


class MetaImporter(HyFinder):
    def find_module(self, fullname, path=None):
        pth = self.find_on_path(fullname)
        if pth is None:
            return
        return MetaLoader()


sys.meta_path.append(MetaImporter())
sys.path.insert(0, "")
