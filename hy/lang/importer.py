from hy.compiler.modfaker import forge_module
from hy.lex.tokenize import tokenize


def _hy_import_file(name, fd):
    m = forge_module(
        name,
        fd,
        tokenize(open(fd, 'r').read())
    )
    return m
