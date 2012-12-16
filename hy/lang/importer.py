from hy.compiler.modfaker import forge_module
from hy.lex.tokenize import tokenize
import sys
import imp
import os


def _hy_import_file(fd):
    name = 'hython file'

    m = forge_module(
        name,
        fd,
        tokenize(open(fd, 'r').read())
    )
    return m



class MetaImporter(object):
    def find_module(self, fullname, path=None):
        lastname = fullname.rsplit(".", 1)[-1]
        for d in path or sys.path:
            hy = os.path.join(d, lastname + ".hy")
            pkg = os.path.join(d, lastname, "__init__.py")
            pkgc = getattr(imp, "cache_from_source",
                           lambda path: path + "c")(pkg)
            if (os.path.exists(hy) and
                not (os.path.exists(pkg) or os.path.exists(pkgc))):
                self.path = hy
                return self
        return None

    def load_module(self, name):
        if name not in sys.modules:
            sys.modules[name] = None
            sys.modules[name] = _hy_import_file(self.path)
            sys.modules[name].__loader__ = self

        return sys.modules[name]

    def is_package(self, name):
        return False


sys.meta_path.append(MetaImporter())
sys.path.insert(0, "")
