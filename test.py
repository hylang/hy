
from hy.lex.tokenize import tokenize

print tokenize("""
(+ 1 1) ; this adds one plus one
(- 1 1) ; this does other things
(print (+ 1 1))
""")
