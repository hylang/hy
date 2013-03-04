#

from hy.lex import tokenize
from hy.compiler import hy_compile
import imp


def import_file_to_module(name, fpath):
    ast = hy_compile(tokenize(open(fpath, 'r').read()))
    mod = imp.new_module(name)
    mod.__file__ = fpath
    eval(compile(ast, fpath, "exec"), mod.__dict__)
    return mod
