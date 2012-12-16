from hy.compiler.modfaker import forge_module
from hy.lex.tokenize import tokenize


m = forge_module(
    'test',
    'test.hy',
    tokenize('(def two (fn [] (print (+ 1 1))))(def x 1)')
)

print m.two
m.two()

print m.x
