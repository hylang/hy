from hy.compiler.modfaker import forge_module
from hy.lex.tokenize import tokenize


m = forge_module(
    'test',
    'test.hy',
    tokenize('(def two (fn [x] (print x)))(two "Hello")')
)

